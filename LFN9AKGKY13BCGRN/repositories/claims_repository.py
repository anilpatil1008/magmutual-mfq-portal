from __future__ import annotations

import pandas as pd

from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql


def _parse_snowflake_object_name(object_name: str) -> tuple[str | None, str | None, str]:
    parts = [part.strip().strip('"') for part in str(object_name).split(".") if part.strip()]
    if len(parts) == 3:
        database, schema, name = parts
        return database.upper(), schema.upper(), name.upper()
    if len(parts) == 2:
        schema, name = parts
        return None, schema.upper(), name.upper()
    if len(parts) == 1:
        return None, None, parts[0].upper()
    raise ValueError(f"Invalid Snowflake object name: {object_name}")


def _quote_identifier(identifier: str) -> str:
    return f'"{str(identifier).replace(chr(34), chr(34) + chr(34))}"'


def _information_schema_prefix(database: str | None) -> str:
    if database:
        return f"{_quote_identifier(database)}.INFORMATION_SCHEMA"
    return "INFORMATION_SCHEMA"


def _schema_predicate(schema: str | None) -> str:
    if schema:
        return f"UPPER(TABLE_SCHEMA) = '{quote_sql(schema)}'"
    return "TABLE_SCHEMA = CURRENT_SCHEMA()"


def object_exists(session, object_name: str) -> bool:
    database, schema, name = _parse_snowflake_object_name(object_name)
    object_q = quote_sql(name)
    information_schema = _information_schema_prefix(database)
    schema_predicate = _schema_predicate(schema)
    df = execute_query_df(
        session,
        f"""
        SELECT 1 AS FOUND FROM {information_schema}.TABLES
        WHERE {schema_predicate} AND UPPER(TABLE_NAME) = '{object_q}'
        UNION ALL
        SELECT 1 AS FOUND FROM {information_schema}.VIEWS
        WHERE {schema_predicate} AND UPPER(TABLE_NAME) = '{object_q}'
        LIMIT 1
        """,
        query_name=f"claims.object_exists.{object_name}",
    )
    return not df.empty


def table_columns(session, table_name: str) -> set[str]:
    if not object_exists(session, table_name):
        return set()
    database, schema, name = _parse_snowflake_object_name(table_name)
    information_schema = _information_schema_prefix(database)
    schema_predicate = _schema_predicate(schema)
    table_q = quote_sql(name)
    df = execute_query_df(
        session,
        f"""
        SELECT COLUMN_NAME
        FROM {information_schema}.COLUMNS
        WHERE {schema_predicate}
          AND UPPER(TABLE_NAME) = '{table_q}'
        """,
        query_name=f"claims.table_columns.{table_name}",
    )
    return {str(v).upper() for v in df.get("COLUMN_NAME", pd.Series(dtype=str)).dropna().tolist()}


CLAIMS_QUEUE_COLUMNS = [
    "CLAIM_ID",
    "PATIENT_DEFENDANT",
    "MFQ_STATUS",
    "WORKFLOW_STATUS",
    "PRIORITY",
    "CLAIM_STATUS",
    "CLAIM_TYPE",
    "DATE_REQUESTED",
    "AI_CONFIDENCE",
]

CLAIM_DETAIL_COLUMNS = [
    "CLAIM_ID",
    "DEFENDANT_ID",
    "STATUS",
    "PRIORITY",
    "PATIENT_NAME",
    "DEFENDANT_NAME",
    "ASSIGNED_TO",
    "FILE_NUMBER",
    "SPECIALTY",
    "DATE_REQUESTED",
    "AI_CONFIDENCE",
]


def _normalize_snowflake_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Snowflake result column labels to unquoted uppercase names."""
    if df.columns.empty:
        return df

    normalized = df.copy()
    normalized.columns = [str(column).strip().strip('"').upper() for column in normalized.columns]

    if not normalized.columns.has_duplicates:
        return normalized

    deduped = pd.DataFrame(index=normalized.index)
    for column in dict.fromkeys(normalized.columns):
        matching = normalized.loc[:, normalized.columns == column]
        deduped[column] = matching.bfill(axis=1).iloc[:, 0] if isinstance(matching, pd.DataFrame) else matching
    return deduped


def get_claims_queue(session) -> pd.DataFrame:
    select_columns = ",\n            ".join(f"{column} AS {column}" for column in CLAIMS_QUEUE_COLUMNS)
    df = execute_query_df(
        session,
        f"""
        SELECT
            {select_columns}
        FROM {obj.MFQ_CLAIMS_LIST_VIEW}
        ORDER BY DATE_REQUESTED DESC NULLS LAST
        """,
        query_name="claims.get_claims_queue",
    )
    return _normalize_snowflake_dataframe_columns(df)


def _select_list(columns: list[str]) -> str:
    return ",\n            ".join(f"{column} AS {column}" for column in columns)


def get_claim_details_by_id(session, claim_id: str) -> pd.DataFrame:
    return execute_query_df(
        session,
        f"""
        SELECT
            {_select_list(CLAIM_DETAIL_COLUMNS)}
        FROM {obj.MFQ_CLAIM_DETAIL_VW}
        WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        LIMIT 1
        """,
        params=[str(claim_id)],
        query_name="claims.get_claim_details_by_id",
    )


def get_claim_detail(session, claim_id: str) -> pd.DataFrame:
    return get_claim_details_by_id(session, claim_id)


def get_claim_defendants(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT DEFENDANT_ID, CLAIM_ID, DEFENDANT_NAME FROM {obj.MFQ_CLAIM_DEFENDANTS_TABLE} WHERE CLAIM_ID = '{claim_q}'", query_name="claims.get_claim_defendants")


def get_claim_documents(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,DOCUMENT_ID,DOCUMENT_NAME,DOCUMENT_TYPE,CREATED_TS FROM {obj.MFQ_DOCUMENTS_TABLE} WHERE CLAIM_ID = '{claim_q}' ORDER BY CREATED_TS DESC", query_name="claims.get_claim_documents")


def get_assignment_queue(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,ASSIGNMENT_ID,ASSIGNED_TO,ASSIGNED_AT,ASSIGNMENT_STATUS FROM {obj.MFQ_ASSIGNMENT_QUEUE_VIEW} WHERE CLAIM_ID = '{claim_q}' ORDER BY ASSIGNED_AT DESC", query_name="claims.get_assignment_queue")


def get_status_history(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,STATUS,EVENT_TS,EVENT_NOTE,UPDATED_BY FROM {obj.MFQ_STATUS_HISTORY_TABLE} WHERE CLAIM_ID = '{claim_q}' ORDER BY EVENT_TS DESC", query_name="claims.get_status_history")


def update_claim_status(session, claim_id: str, new_status: str) -> None:
    claim_q = quote_sql(claim_id)
    status_q = quote_sql(new_status)
    session.sql(f"UPDATE {obj.MFQ_CLAIMS_TABLE} SET STATUS = '{status_q}', LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE CLAIM_ID = '{claim_q}'").collect()


def touch_assignment_for_username(session, claim_id: str, assigned_to: str) -> None:
    claim_q = quote_sql(claim_id)
    assigned_q = quote_sql(assigned_to)
    session.sql(f"UPDATE {obj.MFQ_ASSIGNMENTS_TABLE} ca SET LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE CLAIM_ID = '{claim_q}' AND ASSIGNED_TO_USER_ID IN (SELECT USER_ID FROM {obj.MFQ_USERS_TABLE} WHERE USERNAME = '{assigned_q}')").collect()
