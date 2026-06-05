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




CLAIM_FILTER_SELECT_COLUMNS = [
    "CLAIM_ID",
    "PATIENT_DEFENDANT",
    "MFQ_STATUS",
    "PRIORITY",
    "DATE_REQUESTED",
    "AI_CONFIDENCE",
    "CLAIM_TYPE",
    "CLAIM_STATUS",
]


def _coerce_filter_values(value: object) -> list[str]:
    """Return non-empty filter values while tolerating legacy scalar state."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_values = value
    else:
        raw_values = [value]
    return [str(item).strip() for item in raw_values if str(item or "").strip()]


def _add_upper_in_predicate(
    predicates: list[str],
    params: list[object],
    column_name: str,
    values: list[str],
    all_labels: set[str] | None = None,
) -> None:
    filtered_values = [value for value in values if value not in (all_labels or set())]
    if not filtered_values:
        return
    placeholders = ", ".join("?" for _ in filtered_values)
    predicates.append(f"UPPER({column_name}) IN ({placeholders})")
    params.extend(value.upper() for value in filtered_values)


def build_claim_filter_where_clause(filters: dict | None) -> tuple[str, list[object]]:
    """Build a parameterized Snowflake WHERE clause for recent-claims filters."""
    filters = filters or {}
    predicates = ["1 = 1"]
    params: list[object] = []

    selected_statuses = _coerce_filter_values(
        filters.get("selected_statuses", filters.get("selected_status"))
    )
    _add_upper_in_predicate(predicates, params, "MFQ_STATUS", selected_statuses, {"All Statuses"})

    selected_priorities = _coerce_filter_values(
        filters.get("selected_priorities", filters.get("selected_priority"))
    )
    _add_upper_in_predicate(predicates, params, "PRIORITY", selected_priorities, {"All Priorities"})

    selected_claim_types = _coerce_filter_values(filters.get("selected_claim_types"))
    _add_upper_in_predicate(predicates, params, "CLAIM_TYPE", selected_claim_types, {"All Claim Types"})

    selected_ai_confidence_buckets = _coerce_filter_values(
        filters.get("selected_ai_confidence_buckets", filters.get("selected_ai_confidence"))
    )
    selected_ai_confidence_buckets = [
        value for value in selected_ai_confidence_buckets if value != "All Scores"
    ]
    ai_confidence_predicates: list[str] = []
    if "High" in selected_ai_confidence_buckets:
        ai_confidence_predicates.append("AI_CONFIDENCE >= 90")
    if "Medium" in selected_ai_confidence_buckets:
        ai_confidence_predicates.append("(AI_CONFIDENCE >= 80 AND AI_CONFIDENCE < 90)")
    if "Low" in selected_ai_confidence_buckets:
        ai_confidence_predicates.append("AI_CONFIDENCE < 80")
    if ai_confidence_predicates:
        predicates.append("(" + " OR ".join(ai_confidence_predicates) + ")")

    date_requested_from = filters.get("date_requested_from")
    if date_requested_from is not None:
        predicates.append("DATE(DATE_REQUESTED) >= ?")
        params.append(date_requested_from)

    date_requested_to = filters.get("date_requested_to")
    if date_requested_to is not None:
        predicates.append("DATE(DATE_REQUESTED) <= ?")
        params.append(date_requested_to)

    search_text = str(filters.get("search_text") or "").strip()
    if search_text:
        predicates.append(
            "("
            "TO_VARCHAR(CLAIM_ID) ILIKE ? OR "
            "TO_VARCHAR(PATIENT_DEFENDANT) ILIKE ? OR "
            "TO_VARCHAR(MFQ_STATUS) ILIKE ? OR "
            "TO_VARCHAR(PRIORITY) ILIKE ? OR "
            "TO_VARCHAR(CLAIM_TYPE) ILIKE ? OR "
            "TO_VARCHAR(CLAIM_STATUS) ILIKE ?"
            ")"
        )
        params.extend([f"%{search_text}%"] * 6)

    return " WHERE " + " AND ".join(predicates), params


def get_filtered_claims_count(session, filters: dict | None) -> int:
    where_clause, params = build_claim_filter_where_clause(filters)
    df = execute_query_df(
        session,
        f"SELECT COUNT(*) AS TOTAL_COUNT FROM {obj.VW_MFQ_CLAIMS}{where_clause}",
        params=params,
        query_name="claims.get_filtered_claims_count",
    )
    df = _normalize_snowflake_dataframe_columns(df)
    if df.empty or "TOTAL_COUNT" not in df.columns:
        return 0
    return int(df.iloc[0].get("TOTAL_COUNT") or 0)


def get_filtered_recent_claims(session, filters: dict | None, page: int, page_size: int) -> pd.DataFrame:
    where_clause, params = build_claim_filter_where_clause(filters)
    offset = max(0, (max(1, int(page)) - 1) * max(1, int(page_size)))
    select_columns = ",\n            ".join(f"{column} AS {column}" for column in CLAIM_FILTER_SELECT_COLUMNS)
    df = execute_query_df(
        session,
        f"""
        SELECT
            {select_columns}
        FROM {obj.VW_MFQ_CLAIMS}
        {where_clause}
        ORDER BY DATE_REQUESTED DESC NULLS LAST
        LIMIT ? OFFSET ?
        """,
        params=[*params, int(page_size), offset],
        query_name="claims.get_filtered_recent_claims",
    )
    return _normalize_snowflake_dataframe_columns(df)


def get_available_claim_statuses(session) -> list[str]:
    df = execute_query_df(
        session,
        f"""
        SELECT DISTINCT MFQ_STATUS
        FROM {obj.VW_MFQ_CLAIMS}
        WHERE MFQ_STATUS IS NOT NULL
        ORDER BY MFQ_STATUS
        """,
        query_name="claims.get_available_claim_statuses",
    )
    df = _normalize_snowflake_dataframe_columns(df)
    if df.empty or "MFQ_STATUS" not in df.columns:
        return []
    return [str(value).strip() for value in df["MFQ_STATUS"].dropna().tolist() if str(value).strip()]


def get_available_claim_types(session) -> list[str]:
    df = execute_query_df(
        session,
        f"""
        SELECT DISTINCT CLAIM_TYPE
        FROM {obj.VW_MFQ_CLAIMS}
        WHERE CLAIM_TYPE IS NOT NULL
        ORDER BY CLAIM_TYPE
        """,
        query_name="claims.get_available_claim_types",
    )
    df = _normalize_snowflake_dataframe_columns(df)
    if df.empty or "CLAIM_TYPE" not in df.columns:
        return []
    return [str(value).strip() for value in df["CLAIM_TYPE"].dropna().tolist() if str(value).strip()]


def get_claim_detail(session, claim_id: str) -> pd.DataFrame:
    return execute_query_df(
        session,
        f"""
        SELECT *
        FROM {obj.MFQ_CLAIM_DETAIL_VW}
        WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        """,
        params=[str(claim_id)],
        query_name="claims.get_claim_detail",
    )


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
