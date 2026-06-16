from __future__ import annotations

import pandas as pd
import streamlit as st

from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql
from utils.claim_lifecycle import claim_bucket_sql_predicate


def _safe_int(value, default: int = 0) -> int:
    """Return a safe integer count value for Snowflake/Pandas results."""
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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


@st.cache_data(ttl=1800, show_spinner=False)
def _object_exists_cached(_session, session_cache_key: str, object_name: str) -> bool:
    database, schema, name = _parse_snowflake_object_name(object_name)
    object_q = quote_sql(name)
    information_schema = _information_schema_prefix(database)
    schema_predicate = _schema_predicate(schema)
    df = execute_query_df(
        _session,
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


def _object_exists_cache_scope(session) -> str:
    """Return a stable scope so object existence checks survive reruns.

    Streamlit can recreate Snowpark wrapper objects between reruns, making
    ``id(session)`` too volatile for cache keys. Object visibility is primarily
    scoped by Snowflake user/role/database/schema, so prefer those values when
    available and fall back to a process-local scope for tests.
    """
    parts = []
    for attr_name in ("get_current_user", "get_current_role", "get_current_database", "get_current_schema"):
        getter = getattr(session, attr_name, None)
        if callable(getter):
            try:
                parts.append(str(getter() or "").upper())
            except Exception:
                parts.append("")
    scope = ":".join(part for part in parts if part)
    return scope or "default"


def object_exists(session, object_name: str) -> bool:
    return _object_exists_cached(session, _object_exists_cache_scope(session), str(object_name).upper())


@st.cache_data(ttl=1800, show_spinner=False)
def _table_columns_cached(_session, session_cache_key: str, table_name: str) -> set[str]:
    if not object_exists(_session, table_name):
        return set()
    database, schema, name = _parse_snowflake_object_name(table_name)
    information_schema = _information_schema_prefix(database)
    schema_predicate = _schema_predicate(schema)
    table_q = quote_sql(name)
    df = execute_query_df(
        _session,
        f"""
        SELECT COLUMN_NAME
        FROM {information_schema}.COLUMNS
        WHERE {schema_predicate}
          AND UPPER(TABLE_NAME) = '{table_q}'
        """,
        query_name=f"claims.table_columns.{table_name}",
    )
    return {str(v).upper() for v in df.get("COLUMN_NAME", pd.Series(dtype=str)).dropna().tolist()}


def table_columns(session, table_name: str) -> set[str]:
    return _table_columns_cached(session, str(id(session)), str(table_name))


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
    "FILE_NUMBER",
    "DEFENDANT_NAME",
    "PATIENT_DEFENDANT",
    "MFQ_STATUS",
    "WORKFLOW_STATUS",
    "PRIORITY",
    "CLAIM_PRIORITY",
    "DATE_REQUESTED",
    "AI_CONFIDENCE",
    "CLAIM_TYPE",
    "CLAIM_STATUS",
]


def get_recent_claims_dataset(session) -> pd.DataFrame:
    """Return all visible recent-claims rows for cached, in-memory UI filtering."""
    available_columns = table_columns(session, obj.VW_MFQ_CLAIMS)
    select_columns = _select_columns_for_available_view(CLAIM_FILTER_SELECT_COLUMNS, available_columns)
    order_by_clause = (
        "ORDER BY DATE_REQUESTED DESC NULLS LAST"
        if "DATE_REQUESTED" in available_columns
        else "ORDER BY CLAIM_ID"
    )
    df = execute_query_df(
        session,
        f"""
        SELECT
            {select_columns}
        FROM {obj.VW_MFQ_CLAIMS}
        {order_by_clause}
        """,
        query_name="claims.get_recent_claims_dataset",
    )
    return _normalize_snowflake_dataframe_columns(df)


def _coerce_filter_values(value: object) -> list[str]:
    """Return non-empty filter values while tolerating legacy scalar state."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_values = value
    else:
        raw_values = [value]
    return [str(item).strip() for item in raw_values if str(item or "").strip()]


def _has_column(available_columns: set[str] | None, column_name: str) -> bool:
    return available_columns is None or column_name.upper() in available_columns


def _select_columns_for_available_view(desired_columns: list[str], available_columns: set[str]) -> str:
    """Select stable dashboard columns while tolerating older deployed view shapes."""
    select_expressions: list[str] = []
    for column in desired_columns:
        if column.upper() in available_columns:
            if column.upper() == "AI_CONFIDENCE":
                select_expressions.append(
                    "IFF(TRY_TO_DOUBLE(AI_CONFIDENCE) BETWEEN 0 AND 1, "
                    "TRY_TO_DOUBLE(AI_CONFIDENCE) * 100, TRY_TO_DOUBLE(AI_CONFIDENCE)) AS AI_CONFIDENCE"
                )
            else:
                select_expressions.append(f"{column} AS {column}")
        else:
            select_expressions.append(f"NULL AS {column}")
    return ",\n            ".join(select_expressions)


def _add_upper_in_predicate(
    predicates: list[str],
    params: list[object],
    column_name: str,
    values: list[str],
    all_labels: set[str] | None = None,
    available_columns: set[str] | None = None,
) -> None:
    filtered_values = [value for value in values if value not in (all_labels or set())]
    if not filtered_values or not _has_column(available_columns, column_name):
        return
    placeholders = ", ".join("?" for _ in filtered_values)
    predicates.append(f"UPPER({column_name}) IN ({placeholders})")
    params.extend(value.upper() for value in filtered_values)


def build_claim_filter_where_clause(
    filters: dict | None, available_columns: set[str] | None = None
) -> tuple[str, list[object]]:
    """Build a parameterized Snowflake WHERE clause for recent-claims filters."""
    filters = filters or {}
    predicates = ["1 = 1"]
    params: list[object] = []

    selected_statuses = _coerce_filter_values(
        filters.get("selected_statuses", filters.get("selected_status"))
    )
    _add_upper_in_predicate(
        predicates, params, "MFQ_STATUS", selected_statuses, {"All Statuses"}, available_columns
    )

    selected_priorities = _coerce_filter_values(
        filters.get("selected_priorities", filters.get("selected_priority"))
    )
    _add_upper_in_predicate(
        predicates, params, "PRIORITY", selected_priorities, {"All Priorities"}, available_columns
    )

    selected_claim_types = _coerce_filter_values(filters.get("selected_claim_types"))
    _add_upper_in_predicate(
        predicates, params, "CLAIM_TYPE", selected_claim_types, {"All Claim Types"}, available_columns
    )

    selected_ai_confidence_buckets = _coerce_filter_values(
        filters.get("selected_ai_confidence_buckets", filters.get("selected_ai_confidence"))
    )
    selected_ai_confidence_buckets = [
        value for value in selected_ai_confidence_buckets if value != "All Scores"
    ]
    ai_confidence_predicates: list[str] = []
    if _has_column(available_columns, "AI_CONFIDENCE"):
        if "High" in selected_ai_confidence_buckets:
            ai_confidence_predicates.append("AI_CONFIDENCE >= 90")
        if "Medium" in selected_ai_confidence_buckets:
            ai_confidence_predicates.append("(AI_CONFIDENCE >= 80 AND AI_CONFIDENCE < 90)")
        if "Low" in selected_ai_confidence_buckets:
            ai_confidence_predicates.append("AI_CONFIDENCE < 80")
    if ai_confidence_predicates:
        predicates.append("(" + " OR ".join(ai_confidence_predicates) + ")")

    due_date_from = filters.get("due_date_from")
    if due_date_from is not None and _has_column(available_columns, "DUE_DATE"):
        predicates.append("DATE(DUE_DATE) >= ?")
        params.append(due_date_from)

    due_date_to = filters.get("due_date_to")
    if due_date_to is not None and _has_column(available_columns, "DUE_DATE"):
        predicates.append("DATE(DUE_DATE) <= ?")
        params.append(due_date_to)

    date_requested_from = filters.get("date_requested_from")
    if date_requested_from is not None and _has_column(available_columns, "DATE_REQUESTED"):
        predicates.append("DATE(DATE_REQUESTED) >= ?")
        params.append(date_requested_from)

    date_requested_to = filters.get("date_requested_to")
    if date_requested_to is not None and _has_column(available_columns, "DATE_REQUESTED"):
        predicates.append("DATE(DATE_REQUESTED) <= ?")
        params.append(date_requested_to)

    search_text = str(filters.get("search_text") or "").strip()
    if search_text:
        search_columns = [
            column
            for column in (
                "CLAIM_ID",
                "FILE_NUMBER",
                "PATIENT_DEFENDANT",
                "DEFENDANT_NAME",
                "MFQ_STATUS",
                "WORKFLOW_STATUS",
                "PRIORITY",
                "CLAIM_PRIORITY",
                "CLAIM_TYPE",
                "CLAIM_STATUS",
            )
            if _has_column(available_columns, column)
        ]
        if search_columns:
            predicates.append(
                "(" + " OR ".join(f"TO_VARCHAR({column}) ILIKE ?" for column in search_columns) + ")"
            )
            params.extend([f"%{search_text}%"] * len(search_columns))

    claim_bucket_predicate, claim_bucket_params = claim_bucket_sql_predicate(
        str(filters.get("claim_bucket") or "")
    )
    if claim_bucket_predicate and _has_column(available_columns, "MFQ_STATUS"):
        predicates.append(claim_bucket_predicate)
        params.extend(claim_bucket_params)

    return " WHERE " + " AND ".join(predicates), params


def get_filtered_claim_bucket_counts(session, filters: dict | None) -> dict[str, int]:
    """Return Ongoing and History claim counts in one Snowflake query."""
    available_columns = table_columns(session, obj.VW_MFQ_CLAIMS)
    shared_filters = dict(filters or {})
    shared_filters.pop("claim_bucket", None)
    where_clause, params = build_claim_filter_where_clause(
        shared_filters, available_columns
    )
    if "MFQ_STATUS" not in available_columns:
        total_df = execute_query_df(
            session,
            f"SELECT COUNT(*) AS ONGOING_COUNT, 0 AS HISTORY_COUNT FROM {obj.VW_MFQ_CLAIMS}{where_clause}",
            params=params,
            query_name="claims.get_filtered_claim_bucket_counts.no_mfq_status",
        )
    else:
        total_df = execute_query_df(
            session,
            f"""
            SELECT
                SUM(IFF(UPPER(TRIM(COALESCE(MFQ_STATUS, ''))) <> 'APPROVED', 1, 0)) AS ONGOING_COUNT,
                SUM(IFF(UPPER(TRIM(COALESCE(MFQ_STATUS, ''))) = 'APPROVED', 1, 0)) AS HISTORY_COUNT
            FROM {obj.VW_MFQ_CLAIMS}
            {where_clause}
            """,
            params=params,
            query_name="claims.get_filtered_claim_bucket_counts",
        )
    df = _normalize_snowflake_dataframe_columns(total_df)
    if df.empty:
        return {"ongoing": 0, "history": 0}
    row = df.iloc[0]
    return {
        "ongoing": _safe_int(row.get("ONGOING_COUNT")),
        "history": _safe_int(row.get("HISTORY_COUNT")),
    }


def get_filtered_claims_count(session, filters: dict | None) -> int:
    available_columns = table_columns(session, obj.VW_MFQ_CLAIMS)
    where_clause, params = build_claim_filter_where_clause(filters, available_columns)
    df = execute_query_df(
        session,
        f"SELECT COUNT(*) AS TOTAL_COUNT FROM {obj.VW_MFQ_CLAIMS}{where_clause}",
        params=params,
        query_name="claims.get_filtered_claims_count",
    )
    df = _normalize_snowflake_dataframe_columns(df)
    if df.empty or "TOTAL_COUNT" not in df.columns:
        return 0
    return _safe_int(df.iloc[0].get("TOTAL_COUNT"))


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




CLAIM_DETAIL_COLUMNS = [
    "CLAIM_ID",
    "CLAIM_NUMBER",
    "FILE_NUMBER",
    "PATIENT_NAME",
    "PATIENT_DEFENDANT",
    "DEFENDANT_ID",
    "DEFENDANT_NAME",
    "DEFENDANT_SPECIALTY",
    "DEFENDANT_SPECIALITY",
    "SPECIALTY",
    "SPECIALITY",
    "DEFENDANT_TYPE",
    "DEFENDANT_COUNT",
    "SOURCE_FILE_NAME",
    "MFQ_STATUS",
    "WORKFLOW_STATUS",
    "STATUS",
    "CLAIM_STATUS",
    "CLAIM_TYPE",
    "PRIORITY",
    "CLAIM_PRIORITY",
    "DATE_REQUESTED",
    "MAGMUTUAL_CONTACT",
    "MAGMUTUAL_CONTACT_NAME",
    "CONTACT",
    "CONTACT_NAME",
    "MAGMUTUAL_CONTACT_EMAIL",
    "CONTACT_EMAIL",
    "MAGMUTUAL_EMAIL",
    "EMAIL",
    "MAGMUTUAL_CONTACT_PHONE",
    "CONTACT_PHONE",
    "ASSIGNED_TO",
    "AI_CONFIDENCE",
    "DRAWER_NAME",
    "FOLDER_NAME",
    "FIRST_DOCUMENT_DATE",
    "LAST_DOCUMENT_DATE",
    "SOURCE_DOCUMENT_COUNT",
    "DEFENDANT_STATUS",
    "MINIMUM_GATE_STATUS",
    "EMBEDDING_STATUS",
    "LAST_SYNCED_AT",
    "CREATED_AT",
    "CREATED_TS",
    "UPDATED_AT",
    "LAST_UPDATED_TS",
]


def get_claim_detail_by_id(session, claim_id: str) -> pd.DataFrame:
    """Fetch only lightweight claim detail columns for a single selected claim."""
    available_columns = table_columns(session, obj.MFQ_CLAIM_DETAIL_VW)
    select_columns = _select_columns_for_available_view(CLAIM_DETAIL_COLUMNS, available_columns)
    df = execute_query_df(
        session,
        f"""
        SELECT
            {select_columns}
        FROM {obj.MFQ_CLAIM_DETAIL_VW}
        WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        LIMIT 1
        """,
        params=[str(claim_id)],
        query_name="claims.get_claim_detail_by_id",
    )
    return _normalize_snowflake_dataframe_columns(df)


def get_claim_detail(session, claim_id: str) -> pd.DataFrame:
    return get_claim_detail_by_id(session, claim_id)


def get_claim_summary_by_id(session, claim_id: str) -> pd.DataFrame:
    """Compatibility alias for the lightweight single-claim summary query."""
    return get_claim_detail_by_id(session, claim_id)


def get_claim_status_snapshot(session, claim_id: str) -> pd.DataFrame:
    available_columns = table_columns(session, obj.VW_MFQ_CLAIMS)
    select_columns = _select_columns_for_available_view(
        [
            "CLAIM_ID",
            "PATIENT_DEFENDANT",
            "MFQ_STATUS",
            "CLAIM_STATUS",
            "PRIORITY",
            "CLAIM_PRIORITY",
            "CLAIM_TYPE",
            "DATE_REQUESTED",
        ],
        available_columns,
    )
    df = execute_query_df(
        session,
        f"""
        SELECT
            {select_columns}
        FROM {obj.VW_MFQ_CLAIMS}
        WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        """,
        params=[str(claim_id)],
        query_name="claims.get_claim_status_snapshot",
    )
    return _normalize_snowflake_dataframe_columns(df)


def get_claim_defendants(session, claim_id: str) -> pd.DataFrame:
    columns = table_columns(session, obj.MFQ_CLAIM_DEFENDANTS_TABLE)
    specialty_expr = "NULL AS DEFENDANT_SPECIALTY"
    for specialty_column in ("DEFENDANT_SPECIALTY", "DEFENDANT_SPECIALITY", "SPECIALTY", "SPECIALITY"):
        if specialty_column in columns:
            specialty_expr = f"{specialty_column} AS DEFENDANT_SPECIALTY"
            break

    df = execute_query_df(
        session,
        f"""
        SELECT
            DEFENDANT_ID,
            CLAIM_ID,
            DEFENDANT_NAME,
            {specialty_expr}
        FROM {obj.MFQ_CLAIM_DEFENDANTS_TABLE}
        WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        """,
        params=[str(claim_id)],
        query_name="claims.get_claim_defendants",
    )
    return _normalize_snowflake_dataframe_columns(df)


def get_claim_documents_by_id(session, claim_id: str) -> pd.DataFrame:
    return get_claim_documents(session, claim_id)


def get_claim_documents(session, claim_id: str) -> pd.DataFrame:
    df = execute_query_df(
        session,
        f"""
        SELECT CLAIM_ID, DOCUMENT_ID, DOCUMENT_NAME, DOCUMENT_TYPE, CREATED_TS
        FROM {obj.MFQ_DOCUMENTS_TABLE}
        WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        ORDER BY CREATED_TS DESC
        """,
        params=[str(claim_id)],
        query_name="claims.get_claim_documents",
    )
    return _normalize_snowflake_dataframe_columns(df)


def get_claim_history_by_claim_id(session, claim_id: str) -> pd.DataFrame:
    df = execute_query_df(
        session,
        f"""
        SELECT CLAIM_ID, STATUS, EVENT_TS, EVENT_NOTE, UPDATED_BY
        FROM {obj.MFQ_STATUS_HISTORY_TABLE}
        WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        ORDER BY EVENT_TS DESC
        """,
        params=[str(claim_id)],
        query_name="claims.get_claim_history_by_claim_id",
    )
    return _normalize_snowflake_dataframe_columns(df)


def get_assignment_queue(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,ASSIGNMENT_ID,ASSIGNED_TO,ASSIGNED_AT,ASSIGNMENT_STATUS FROM {obj.MFQ_ASSIGNMENT_QUEUE_VIEW} WHERE CLAIM_ID = '{claim_q}' ORDER BY ASSIGNED_AT DESC", query_name="claims.get_assignment_queue")


def get_status_history(session, claim_id: str) -> pd.DataFrame:
    return get_claim_history_by_claim_id(session, claim_id)


def update_claim_status(session, claim_id: str, new_status: str) -> None:
    claim_q = quote_sql(claim_id)
    status_q = quote_sql(new_status)
    session.sql(f"UPDATE {obj.MFQ_CLAIMS_TABLE} SET STATUS = '{status_q}', LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE CLAIM_ID = '{claim_q}'").collect()


def touch_assignment_for_username(session, claim_id: str, assigned_to: str) -> None:
    claim_q = quote_sql(claim_id)
    assigned_q = quote_sql(assigned_to)
    session.sql(f"UPDATE {obj.MFQ_ASSIGNMENTS_TABLE} ca SET LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE CLAIM_ID = '{claim_q}' AND ASSIGNED_TO_USER_ID IN (SELECT USER_ID FROM {obj.MFQ_USERS_TABLE} WHERE USERNAME = '{assigned_q}')").collect()
