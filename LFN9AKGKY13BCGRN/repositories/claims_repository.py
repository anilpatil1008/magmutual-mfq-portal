from __future__ import annotations

import logging

import pandas as pd

from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql

logger = logging.getLogger(__name__)

CLAIM_IDENTIFIER_COLUMNS = ("CLAIM_ID", "CLAIM_NUMBER", "FILE_NUMBER", "FILE_NO")


def get_current_snowflake_context(session) -> dict[str, str]:
    df = execute_query_df(
        session,
        "SELECT CURRENT_DATABASE() AS DATABASE_NAME, CURRENT_SCHEMA() AS SCHEMA_NAME, CURRENT_ROLE() AS ROLE_NAME",
        query_name="claims.current_snowflake_context",
    )
    if df.empty:
        return {"database": "<unknown database>", "schema": "<unknown schema>", "role": "<unknown role>"}
    row = df.iloc[0]
    return {
        "database": str(row.get("DATABASE_NAME") or "<unknown database>"),
        "schema": str(row.get("SCHEMA_NAME") or "<unknown schema>"),
        "role": str(row.get("ROLE_NAME") or "<unknown role>"),
    }


def _object_name_parts(session, object_name: str) -> tuple[str, str, str]:
    context = get_current_snowflake_context(session)
    parts = [part.strip().strip('"').upper() for part in str(object_name).split(".") if part.strip()]
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]
    if len(parts) == 2:
        return context["database"].upper(), parts[0], parts[1]
    return context["database"].upper(), context["schema"].upper(), parts[0] if parts else str(object_name).upper()


def object_location(session, object_name: str) -> str:
    database, schema, _ = _object_name_parts(session, object_name)
    return f"{database}.{schema}"


def object_exists(session, object_name: str) -> bool:
    database, schema, name = _object_name_parts(session, object_name)
    database_q = quote_sql(database)
    schema_q = quote_sql(schema)
    object_q = quote_sql(name)
    df = execute_query_df(
        session,
        f"""
        SELECT 1 AS FOUND
        FROM {database_q}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_CATALOG = '{database_q}'
          AND TABLE_SCHEMA = '{schema_q}'
          AND TABLE_NAME = '{object_q}'
        UNION ALL
        SELECT 1 AS FOUND
        FROM {database_q}.INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_CATALOG = '{database_q}'
          AND TABLE_SCHEMA = '{schema_q}'
          AND TABLE_NAME = '{object_q}'
        LIMIT 1
        """,
        query_name=f"claims.object_exists.{object_name}",
    )
    exists = not df.empty
    if not exists:
        logger.warning("snowflake_object_not_found object=%s location=%s.%s", name, database, schema)
    return exists


def table_columns(session, table_name: str) -> set[str]:
    if not object_exists(session, table_name):
        return set()
    database, schema, name = _object_name_parts(session, table_name)
    df = execute_query_df(
        session,
        f"""
        SELECT COLUMN_NAME
        FROM {quote_sql(database)}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_CATALOG = '{quote_sql(database)}'
          AND TABLE_SCHEMA = '{quote_sql(schema)}'
          AND TABLE_NAME = '{quote_sql(name)}'
        """,
        query_name=f"claims.table_columns.{table_name}",
    )
    return {str(v).upper() for v in df.get("COLUMN_NAME", pd.Series(dtype=str)).dropna().tolist()}


def _identifier_columns_for_object(session, object_name: str) -> list[str]:
    available_cols = table_columns(session, object_name)
    return [col for col in CLAIM_IDENTIFIER_COLUMNS if col in available_cols]


def _normalized_identifier_predicate(columns: list[str], identifiers: list[str]) -> str:
    predicates: list[str] = []
    for column in columns:
        for identifier in identifiers:
            identifier_q = quote_sql(identifier)
            predicates.append(f"TRIM(TO_VARCHAR({column})) = TRIM(TO_VARCHAR('{identifier_q}'))")
    return " OR ".join(predicates) if predicates else "1 = 0"


def _unique_non_empty(values: list[object]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def get_claims_queue(session) -> pd.DataFrame:
    return execute_query_df(
        session,
        f"""SELECT CLAIM_ID,PATIENT_NAME,DEFENDANT_NAME,FILE_NUMBER,STATUS,PRIORITY,ASSIGNED_TO,LAST_UPDATED_TS,DATE_REQUESTED FROM {obj.MFQ_RECENT_CLAIMS_VIEW}""",
        query_name="claims.get_claims_queue",
    )


def get_recent_claim_identifier_candidates(session, selected_claim_id: str) -> list[str]:
    identifiers = _unique_non_empty([selected_claim_id])
    if not object_exists(session, obj.MFQ_RECENT_CLAIMS_VIEW):
        return identifiers

    columns = _identifier_columns_for_object(session, obj.MFQ_RECENT_CLAIMS_VIEW)
    if not columns:
        return identifiers

    selected_q = quote_sql(selected_claim_id)
    select_columns = ", ".join(columns)
    predicate = _normalized_identifier_predicate(columns, [selected_claim_id])
    df = execute_query_df(
        session,
        f"""
        SELECT {select_columns}
        FROM {obj.MFQ_RECENT_CLAIMS_VIEW}
        WHERE {predicate}
        LIMIT 1
        """,
        query_name="claims.get_recent_claim_identifier_candidates",
    )
    if df.empty:
        logger.info("recent_claim_identifier_not_found selected_claim_id=%s", selected_q)
        return identifiers

    row = df.iloc[0]
    return _unique_non_empty([row.get(col) for col in CLAIM_IDENTIFIER_COLUMNS if col in df.columns] + identifiers)


def get_claim_detail(session, claim_id: str, identifier_candidates: list[str] | None = None) -> pd.DataFrame:
    identifiers = _unique_non_empty(identifier_candidates or [claim_id])
    columns = _identifier_columns_for_object(session, obj.MFQ_CLAIM_DETAIL_VIEW)
    predicate = _normalized_identifier_predicate(columns, identifiers)
    return execute_query_df(
        session,
        f"SELECT * FROM {obj.MFQ_CLAIM_DETAIL_VIEW} WHERE {predicate} LIMIT 1",
        query_name="claims.get_claim_detail",
    )


def get_claim_defendants(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT DEFENDANT_ID, CLAIM_ID, DEFENDANT_NAME FROM {obj.MFQ_CLAIM_DEFENDANTS_TABLE} WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR('{claim_q}'))", query_name="claims.get_claim_defendants")


def get_claim_documents(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,DOCUMENT_ID,DOCUMENT_NAME,DOCUMENT_TYPE,CREATED_TS FROM {obj.MFQ_DOCUMENTS_TABLE} WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR('{claim_q}')) ORDER BY CREATED_TS DESC", query_name="claims.get_claim_documents")


def get_assignment_queue(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,ASSIGNMENT_ID,ASSIGNED_TO,ASSIGNED_AT,ASSIGNMENT_STATUS FROM {obj.MFQ_ASSIGNMENT_QUEUE_VIEW} WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR('{claim_q}')) ORDER BY ASSIGNED_AT DESC", query_name="claims.get_assignment_queue")


def get_status_history(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,STATUS,EVENT_TS,EVENT_NOTE,UPDATED_BY FROM {obj.MFQ_STATUS_HISTORY_TABLE} WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR('{claim_q}')) ORDER BY EVENT_TS DESC", query_name="claims.get_status_history")


def update_claim_status(session, claim_id: str, new_status: str) -> None:
    claim_q = quote_sql(claim_id)
    status_q = quote_sql(new_status)
    session.sql(f"UPDATE {obj.MFQ_CLAIMS_TABLE} SET STATUS = '{status_q}', LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR('{claim_q}'))").collect()


def touch_assignment_for_username(session, claim_id: str, assigned_to: str) -> None:
    claim_q = quote_sql(claim_id)
    assigned_q = quote_sql(assigned_to)
    session.sql(f"UPDATE {obj.MFQ_ASSIGNMENTS_TABLE} ca SET LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR('{claim_q}')) AND ASSIGNED_TO_USER_ID IN (SELECT USER_ID FROM {obj.MFQ_USERS_TABLE} WHERE USERNAME = '{assigned_q}')").collect()
