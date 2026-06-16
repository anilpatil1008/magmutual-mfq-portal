from __future__ import annotations

import json
import logging
from time import perf_counter
from typing import Any

import pandas as pd

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from config import column_mappings as col
from config import snowflake_objects as obj
from repositories import assignment_repository, claims_repository, mfq_repository
from services.snowflake_service import quote_sql, safe_collect_df
from utils.claim_lifecycle import classify_claim_bucket
from utils.streamlit_compat import is_debug_enabled


CLAIMS_VIEW = obj.MFQ_RECENT_CLAIMS_VIEW
DETAIL_VIEW = obj.MFQ_CLAIM_DETAIL_VW
FORM_VIEW = obj.MFQ_FORM_WORKSPACE_VIEW
SECTIONS_TABLE = obj.MFQ_SECTIONS_TABLE
QUESTIONS_TABLE = obj.MFQ_QUESTIONS_TABLE
ANSWERS_TABLE = obj.MFQ_ANSWERS_TABLE
QUESTION_CONFIDENCE_TABLE = obj.MFQ_QUESTION_CONFIDENCE_TABLE
SECTION_CONFIDENCE_TABLE = obj.MFQ_SECTION_CONFIDENCE_TABLE
LLM_EVAL_TABLE = obj.LLM_EVALUATION_TABLE

logger = logging.getLogger(__name__)

CLAIMS_SEARCH_INDEX_COLUMN = "_CLAIMS_SEARCH_TEXT"
CLAIMS_BUCKET_COLUMN = "_CLAIMS_BUCKET"
CLAIMS_DATE_REQUESTED_DATE_COLUMN = "_DATE_REQUESTED_DATE"
CLAIMS_AI_CONFIDENCE_NUM_COLUMN = "_AI_CONFIDENCE_NUM"
CLAIMS_SEARCHABLE_COLUMNS = (
    "CLAIM_ID",
    "FILE_NUMBER",
    "PATIENT_DEFENDANT",
    "DEFENDANT_NAME",
    "MFQ_STATUS",
    "WORKFLOW_STATUS",
    "PRIORITY",
    "CLAIM_PRIORITY",
    "CLAIM_STATUS",
    "CLAIM_TYPE",
    "DATE_REQUESTED",
    "AI_CONFIDENCE",
)


def _claims_cache_scope(session: object | None = None) -> str:
    """Key cached claims by app role/context and runtime session without hashing Snowpark."""
    role_scope = str(st.session_state.get("selected_app_role") or st.session_state.get("selected_sf_role") or "default")
    session_scope = str(id(session)) if session is not None else "no-session"
    return f"{role_scope}:{session_scope}"


def _in_streamlit_runtime() -> bool:
    return get_script_run_ctx(suppress_warning=True) is not None


def _normalize_search_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.dt.strftime("%Y-%m-%d").fillna("").str.lower()
    return series.fillna("").astype(str).str.lower()




def _normalize_claim_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mirror known Snowflake columns to uppercase names without changing queries."""
    if df.empty:
        return df
    normalized = df.copy()
    case_map = {str(column).casefold(): column for column in normalized.columns}
    for target in CLAIMS_SEARCHABLE_COLUMNS:
        actual = case_map.get(target.casefold())
        if actual is not None and actual != target and target not in normalized.columns:
            normalized[target] = normalized[actual]
    if "PRIORITY" not in normalized.columns and "CLAIM_PRIORITY" in normalized.columns:
        normalized["PRIORITY"] = normalized["CLAIM_PRIORITY"]
    if "CLAIM_ID" not in normalized.columns and "FILE_NUMBER" in normalized.columns:
        normalized["CLAIM_ID"] = normalized["FILE_NUMBER"]
    return normalized

def add_claims_search_index(df: pd.DataFrame, search_columns: tuple[str, ...] = CLAIMS_SEARCHABLE_COLUMNS) -> pd.DataFrame:
    """Copy a claims dataframe and precompute values reused by dashboard filtering."""
    indexed = _normalize_claim_dataframe_columns(df)
    if indexed.empty:
        indexed[CLAIMS_SEARCH_INDEX_COLUMN] = pd.Series(dtype=str)
        indexed[CLAIMS_BUCKET_COLUMN] = pd.Series(dtype=str)
        indexed[CLAIMS_DATE_REQUESTED_DATE_COLUMN] = pd.Series(dtype=object)
        indexed[CLAIMS_AI_CONFIDENCE_NUM_COLUMN] = pd.Series(dtype=float)
        return indexed

    normalized_columns = [column for column in search_columns if column in indexed.columns]
    indexed[CLAIMS_SEARCH_INDEX_COLUMN] = (
        pd.concat([_normalize_search_series(indexed[column]) for column in normalized_columns], axis=1).agg(" ".join, axis=1)
        if normalized_columns
        else ""
    )
    indexed[CLAIMS_BUCKET_COLUMN] = indexed.apply(classify_claim_bucket, axis=1)
    if "DATE_REQUESTED" in indexed.columns:
        indexed[CLAIMS_DATE_REQUESTED_DATE_COLUMN] = pd.to_datetime(indexed["DATE_REQUESTED"], errors="coerce").dt.date
    else:
        indexed[CLAIMS_DATE_REQUESTED_DATE_COLUMN] = None
    if "AI_CONFIDENCE" in indexed.columns:
        indexed[CLAIMS_AI_CONFIDENCE_NUM_COLUMN] = pd.to_numeric(indexed["AI_CONFIDENCE"], errors="coerce")
    else:
        indexed[CLAIMS_AI_CONFIDENCE_NUM_COLUMN] = pd.NA
    return indexed


def filter_claims_by_search(df: pd.DataFrame, search_text: str) -> pd.DataFrame:
    """Filter claims locally with a precomputed lowercase search index."""
    needle = str(search_text or "").strip().lower()
    if not needle or df.empty:
        return df

    indexed = df if CLAIMS_SEARCH_INDEX_COLUMN in df.columns else add_claims_search_index(df)
    return indexed[indexed[CLAIMS_SEARCH_INDEX_COLUMN].str.contains(needle, regex=False, na=False)]


def _coerce_filter_values(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_values = value
    else:
        raw_values = [value]
    return [str(item).strip() for item in raw_values if str(item or "").strip()]


@st.cache_data(ttl=300, show_spinner="Loading claims...")
def _load_claims_queue_cached(_session, cache_scope: str) -> pd.DataFrame:
    del cache_scope
    return add_claims_search_index(claims_repository.get_claims_queue(_session))


@st.cache_data(ttl=300, show_spinner="Loading claims...")
def _load_recent_claims_cached(_session, cache_scope: str) -> pd.DataFrame:
    del cache_scope
    return add_claims_search_index(claims_repository.get_recent_claims_dataset(_session))


@st.cache_data(ttl=1800, show_spinner=False)
def _object_exists_cached(_session, cache_scope: str, object_name: str) -> bool:
    del cache_scope
    return claims_repository.object_exists(_session, object_name)


def _object_exists(session, object_name: str) -> bool:
    if _in_streamlit_runtime():
        return _object_exists_cached(session, _claims_cache_scope(session), str(object_name))
    return claims_repository.object_exists(session, object_name)


@st.cache_data(ttl=1800, show_spinner=False)
def _table_columns_cached(_session, cache_scope: str, table_name: str) -> set[str]:
    del cache_scope
    return claims_repository.table_columns(_session, table_name)


def _table_columns(session, table_name: str) -> set[str]:
    if _in_streamlit_runtime():
        return _table_columns_cached(session, _claims_cache_scope(session), str(table_name))
    return claims_repository.table_columns(session, table_name)


def _safe_read(session, object_name: str, sql: str, missing_objects: list[str]) -> pd.DataFrame:
    if not _object_exists(session, object_name):
        missing_objects.append(object_name)
        return pd.DataFrame()
    return safe_collect_df(session, sql)


def _sort_claims_queue(queue: pd.DataFrame) -> pd.DataFrame:
    """Sort claims by the best available recency column without assuming a view shape."""
    for sort_column in ("DATE_REQUESTED", col.LAST_UPDATED_TS, "CREATED_TS"):
        if sort_column in queue.columns:
            return queue.sort_values(sort_column, ascending=False, na_position="last")
    return queue


def get_claims_queue(session, username: str, search_text: str = "", status_filter: str = "All") -> pd.DataFrame:
    started = perf_counter()
    df = (
        _load_claims_queue_cached(session, _claims_cache_scope(session))
        if _in_streamlit_runtime()
        else add_claims_search_index(claims_repository.get_claims_queue(session))
    )
    if df.empty:
        logger.info("get_claims_queue_ms=%d rows=0", int((perf_counter() - started) * 1000))
        return df

    scoped = df.copy()
    scoped = filter_claims_by_search(scoped, search_text)

    if status_filter != "All" and "CLAIM_STATUS" in scoped.columns:
        scoped = scoped[scoped["CLAIM_STATUS"] == status_filter]

    result = _sort_claims_queue(scoped)
    logger.info("get_claims_queue_ms=%d rows=%d", int((perf_counter() - started) * 1000), len(result))
    return result




def build_claim_filter_where_clause(filters: dict | None) -> tuple[str, list[object]]:
    return claims_repository.build_claim_filter_where_clause(filters)



def get_cached_recent_claims(session) -> pd.DataFrame:
    """Load recent claims once per cache scope for fast in-memory dashboard filtering."""
    if _in_streamlit_runtime():
        return _load_recent_claims_cached(session, _claims_cache_scope(session))
    return add_claims_search_index(claims_repository.get_recent_claims_dataset(session))


def _local_filter_values(df: pd.DataFrame, column_name: str, values: list[str], all_labels: set[str]) -> pd.DataFrame:
    filtered_values = [str(value).strip() for value in values if str(value).strip() and value not in all_labels]
    if not filtered_values or column_name not in df.columns:
        return df
    selected = {value.upper() for value in filtered_values}
    return df[df[column_name].fillna("").astype(str).str.upper().isin(selected)]


def _local_dashboard_filters(df: pd.DataFrame, filters: dict | None) -> pd.DataFrame:
    filters = filters or {}
    scoped = df
    scoped = _local_filter_values(scoped, "MFQ_STATUS", _coerce_filter_values(filters.get("selected_statuses")), {"All Statuses"})
    scoped = _local_filter_values(scoped, "PRIORITY", _coerce_filter_values(filters.get("selected_priorities")), {"All Priorities"})
    scoped = _local_filter_values(scoped, "CLAIM_TYPE", _coerce_filter_values(filters.get("selected_claim_types")), {"All Claim Types"})

    confidence_buckets = [value for value in _coerce_filter_values(filters.get("selected_ai_confidence_buckets")) if value != "All Scores"]
    if confidence_buckets and "AI_CONFIDENCE" in scoped.columns:
        confidence = (
            scoped[CLAIMS_AI_CONFIDENCE_NUM_COLUMN]
            if CLAIMS_AI_CONFIDENCE_NUM_COLUMN in scoped.columns
            else pd.to_numeric(scoped["AI_CONFIDENCE"], errors="coerce")
        )
        confidence_mask = pd.Series(False, index=scoped.index)
        if "High" in confidence_buckets:
            confidence_mask = confidence_mask | (confidence >= 90)
        if "Medium" in confidence_buckets:
            confidence_mask = confidence_mask | ((confidence >= 80) & (confidence < 90))
        if "Low" in confidence_buckets:
            confidence_mask = confidence_mask | (confidence < 80)
        scoped = scoped[confidence_mask]

    date_requested_from = filters.get("date_requested_from")
    date_requested_to = filters.get("date_requested_to")
    if (date_requested_from is not None or date_requested_to is not None) and "DATE_REQUESTED" in scoped.columns:
        requested_dates = (
            scoped[CLAIMS_DATE_REQUESTED_DATE_COLUMN]
            if CLAIMS_DATE_REQUESTED_DATE_COLUMN in scoped.columns
            else pd.to_datetime(scoped["DATE_REQUESTED"], errors="coerce").dt.date
        )
        if date_requested_from is not None:
            scoped = scoped[requested_dates >= date_requested_from]
            requested_dates = requested_dates.loc[scoped.index]
        if date_requested_to is not None:
            scoped = scoped[requested_dates <= date_requested_to]

    claim_bucket = str(filters.get("claim_bucket") or "").strip().lower()
    if claim_bucket in {"ongoing", "history"}:
        if CLAIMS_BUCKET_COLUMN in scoped.columns:
            scoped = scoped[scoped[CLAIMS_BUCKET_COLUMN] == claim_bucket]
        else:
            bucket_values = scoped.apply(classify_claim_bucket, axis=1)
            scoped = scoped[bucket_values == claim_bucket]

    return filter_claims_by_search(scoped, str(filters.get("search_text") or ""))


def get_filtered_recent_claims_local_all(claims: pd.DataFrame, filters: dict | None) -> pd.DataFrame:
    """Return locally filtered dashboard rows without paginating the result set."""
    return _local_dashboard_filters(claims, filters).copy()


def get_recent_claims_by_bucket_local(
    claims: pd.DataFrame,
    filters: dict | None,
    bucket_search_text: dict[str, str],
) -> dict[str, pd.DataFrame]:
    """Apply shared dashboard filters once, then split/search each claim bucket locally."""
    shared_filters = dict(filters or {})
    shared_filters.pop("claim_bucket", None)
    shared_filters.pop("search_text", None)
    shared = _local_dashboard_filters(claims, shared_filters)
    bucketed: dict[str, pd.DataFrame] = {}
    for bucket, search_text in bucket_search_text.items():
        normalized_bucket = str(bucket or "").strip().lower()
        if CLAIMS_BUCKET_COLUMN in shared.columns and normalized_bucket in {"ongoing", "history"}:
            rows = shared[shared[CLAIMS_BUCKET_COLUMN] == normalized_bucket]
        else:
            rows = _local_dashboard_filters(shared, {"claim_bucket": normalized_bucket})
        bucketed[normalized_bucket] = filter_claims_by_search(rows, search_text).copy()
    return bucketed


@st.cache_data(ttl=120, show_spinner=False)
def _get_filtered_claim_bucket_counts_cached(
    _session, cache_scope: str, filters: dict | None
) -> dict[str, int]:
    del cache_scope
    return claims_repository.get_filtered_claim_bucket_counts(_session, filters)


def get_filtered_claim_bucket_counts(session, filters: dict | None) -> dict[str, int]:
    if _in_streamlit_runtime():
        return _get_filtered_claim_bucket_counts_cached(
            session, _claims_cache_scope(session), filters or {}
        )
    return claims_repository.get_filtered_claim_bucket_counts(session, filters)


def get_filtered_claims_count(session, filters: dict | None) -> int:
    if _in_streamlit_runtime():
        return _get_filtered_claims_count_cached(session, _claims_cache_scope(session), filters or {})
    return claims_repository.get_filtered_claims_count(session, filters)


@st.cache_data(ttl=1800, show_spinner=False)
def _get_available_claim_statuses_cached(_session, cache_scope: str) -> list[str]:
    del cache_scope
    return claims_repository.get_available_claim_statuses(_session)


@st.cache_data(ttl=1800, show_spinner=False)
def _get_available_claim_types_cached(_session, cache_scope: str) -> list[str]:
    del cache_scope
    return claims_repository.get_available_claim_types(_session)


def get_available_claim_statuses(session) -> list[str]:
    if _in_streamlit_runtime():
        return _get_available_claim_statuses_cached(session, _claims_cache_scope(session))
    return claims_repository.get_available_claim_statuses(session)


def get_available_claim_types(session) -> list[str]:
    if _in_streamlit_runtime():
        return _get_available_claim_types_cached(session, _claims_cache_scope(session))
    return claims_repository.get_available_claim_types(session)


def get_claim_details(session, claim_id: str) -> dict[str, Any] | None:
    return get_claim_detail_by_id(session, claim_id)


def _is_blank_value(value: Any) -> bool:
    return value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip().lower() in {"", "-", "nan", "none", "null"}


def _fetch_claim_detail_by_id(session, claim_id: str) -> dict[str, Any] | None:
    started = perf_counter()
    df = claims_repository.get_claim_detail_by_id(session, claim_id)
    detail = df.iloc[0].to_dict() if not df.empty else None
    if detail is not None and _object_exists(session, obj.VW_MFQ_CLAIMS):
        status_df = claims_repository.get_claim_status_snapshot(session, claim_id)
        if not status_df.empty:
            snapshot = status_df.iloc[0].to_dict()
            if not _is_blank_value(snapshot.get("MFQ_STATUS")):
                detail["MFQ_STATUS"] = snapshot.get("MFQ_STATUS")
            for key, value in snapshot.items():
                if key == "MFQ_STATUS":
                    continue
                if _is_blank_value(detail.get(key)):
                    detail[key] = value
    if detail is not None and _object_exists(session, obj.MFQ_CLAIM_DEFENDANTS_TABLE):
        defendant_df = claims_repository.get_claim_defendants(session, claim_id)
        if not defendant_df.empty:
            for key, value in defendant_df.iloc[0].to_dict().items():
                if _is_blank_value(detail.get(key)):
                    detail[key] = value
    if is_debug_enabled():
        logger.info(
            "claim_summary_query_ms=%d selected_claim_id=%s raw_mfq_status=%s",
            int((perf_counter() - started) * 1000),
            claim_id,
            "" if detail is None else str(detail.get("MFQ_STATUS") or "").strip(),
        )
    return detail


@st.cache_data(ttl=300, show_spinner=False)
def _load_claim_detail_by_id_cached(_session, cache_scope: str, claim_id: str) -> dict[str, Any] | None:
    del cache_scope
    return _fetch_claim_detail_by_id(_session, claim_id)


def clear_claim_read_caches() -> None:
    """Clear cached read models after a write that can change claim/dashboard data."""
    _load_recent_claims_cached.clear()
    _load_claims_queue_cached.clear()
    _get_filtered_claims_count_cached.clear()
    _get_filtered_claim_bucket_counts_cached.clear()
    _get_available_claim_statuses_cached.clear()
    _get_available_claim_types_cached.clear()
    _load_claim_detail_by_id_cached.clear()
    if _in_streamlit_runtime():
        current_version = int(st.session_state.get("dashboard_metrics_cache_version", 0) or 0)
        st.session_state["dashboard_metrics_cache_version"] = current_version + 1


def get_claim_summary_by_id(session, claim_id: str) -> dict[str, Any] | None:
    return get_claim_detail_by_id(session, claim_id)


def get_claim_detail_by_id(session, claim_id: str) -> dict[str, Any] | None:
    normalized_claim_id = str(claim_id or "").strip()
    if not normalized_claim_id:
        return None
    if _in_streamlit_runtime():
        return _load_claim_detail_by_id_cached(session, _claims_cache_scope(session), normalized_claim_id)
    return _fetch_claim_detail_by_id(session, normalized_claim_id)


@st.cache_data(ttl=1800, show_spinner=False)
def _get_active_mfq_sections_and_questions_cached(_session, cache_scope: str) -> pd.DataFrame:
    del cache_scope
    started = perf_counter()
    df = mfq_repository.get_active_mfq_sections_and_questions(_session)
    logger.info("get_active_mfq_sections_and_questions_ms=%d rows=%d", int((perf_counter() - started) * 1000), len(df))
    return df


def get_claim_sections_by_id(session, claim_id: str) -> pd.DataFrame:
    del claim_id
    return get_active_mfq_sections_and_questions(session)


def get_claim_questions_by_id(session, claim_id: str) -> pd.DataFrame:
    del claim_id
    return get_active_mfq_sections_and_questions(session)


def get_active_mfq_sections_and_questions(session) -> pd.DataFrame:
    if _in_streamlit_runtime():
        return _get_active_mfq_sections_and_questions_cached(session, _claims_cache_scope(session))
    return mfq_repository.get_active_mfq_sections_and_questions(session)


def get_mfq_sections(session) -> pd.DataFrame:
    return get_active_mfq_sections_and_questions(session)


def _session_claim_cache(cache_name: str) -> dict[str, Any]:
    cache = st.session_state.get(cache_name) if _in_streamlit_runtime() else None
    if not isinstance(cache, dict):
        cache = {}
        if _in_streamlit_runtime():
            st.session_state[cache_name] = cache
    return cache


def get_claim_answers_by_id(session, claim_id: str) -> pd.DataFrame:
    return get_current_mfq_answers_by_claim_id(session, claim_id)


def get_current_mfq_answers_by_claim_id(session, claim_id: str) -> pd.DataFrame:
    started = perf_counter()
    df = mfq_repository.get_current_mfq_answers_by_claim_id(session, claim_id)
    logger.info("get_current_mfq_answers_by_claim_id_ms=%d claim_id=%s rows=%d", int((perf_counter() - started) * 1000), claim_id, len(df))
    return df


def get_mfq_answers_by_claim_id(session, claim_id: str) -> pd.DataFrame:
    return get_current_mfq_answers_by_claim_id(session, claim_id)


def get_claim_history_by_claim_id(session, claim_id: str) -> pd.DataFrame:
    started = perf_counter()
    df = claims_repository.get_claim_history_by_claim_id(session, claim_id)
    logger.info("get_claim_history_by_claim_id_ms=%d claim_id=%s rows=%d", int((perf_counter() - started) * 1000), claim_id, len(df))
    return df


def get_claim_documents_by_id(session, claim_id: str) -> pd.DataFrame:
    return get_claim_documents_by_claim_id(session, claim_id)


def get_claim_documents_by_claim_id(session, claim_id: str) -> pd.DataFrame:
    started = perf_counter()
    df = claims_repository.get_claim_documents(session, claim_id)
    logger.info("get_claim_documents_by_claim_id_ms=%d claim_id=%s rows=%d", int((perf_counter() - started) * 1000), claim_id, len(df))
    return df


def _summary_df_to_map(summary_df: pd.DataFrame) -> dict[str, str]:
    summary_map: dict[str, str] = {}
    if not summary_df.empty:
        for _, row in summary_df.iterrows():
            summary_type = str(row.get("SUMMARY_TYPE", "")).strip().upper()
            if summary_type and summary_type not in summary_map:
                summary_map[summary_type] = str(row.get("SUMMARY_TEXT", "") or "")
    return summary_map


def get_claim_summaries_by_claim_id(session, claim_id: str) -> dict[str, str]:
    started = perf_counter()
    summary_df = mfq_repository.get_claim_summaries(session, claim_id)
    summary_map = _summary_df_to_map(summary_df)
    logger.info("get_claim_summaries_by_claim_id_ms=%d claim_id=%s rows=%d", int((perf_counter() - started) * 1000), claim_id, len(summary_df))
    return summary_map


def get_claim_summary_by_type(session, claim_id: str, summary_type: str) -> str:
    started = perf_counter()
    summary_df = mfq_repository.get_claim_summary_by_type(session, claim_id, summary_type)
    summary_map = _summary_df_to_map(summary_df)
    normalized_type = "RECORD_SUMMARY" if str(summary_type or "").strip().upper() == "RECORDS_SUMMARY" else str(summary_type or "").strip().upper()
    logger.info(
        "get_claim_summary_by_type_ms=%d claim_id=%s summary_type=%s rows=%d",
        int((perf_counter() - started) * 1000),
        claim_id,
        normalized_type,
        len(summary_df),
    )
    return summary_map.get(normalized_type, "")


def _mfq_required_objects_available(session) -> tuple[bool, list[str]]:
    required = [SECTIONS_TABLE, QUESTIONS_TABLE, ANSWERS_TABLE]
    missing = [name for name in required if not _object_exists(session, name)]
    return not missing, missing


def _merge_mfq_sections_answers(sections_df: pd.DataFrame, answers_df: pd.DataFrame) -> pd.DataFrame:
    if sections_df.empty:
        return sections_df
    merged = sections_df.copy()
    if not answers_df.empty:
        answer_rows = answers_df.copy()
        if "UPDATED_AT" in answer_rows.columns:
            answer_rows = answer_rows.sort_values("UPDATED_AT", ascending=False, na_position="last")
        answer_rows = answer_rows.drop_duplicates(subset=["QUESTION_ID"], keep="first")
        merged = merged.merge(answer_rows, on="QUESTION_ID", how="left", suffixes=("", "_ANSWER"))
    else:
        for column in (
            "ANSWER_ID",
            "RUN_ID",
            "RUN_SCOPE",
            "RUN_TYPE",
            "VERSION_NUMBER",
            "IS_CURRENT",
            "SUPERSEDED_BY_ANSWER_ID",
            "CLAIM_ID",
            "DEFENDANT_ID",
            "ANSWER_SECTION_ID",
            "PACKET_ID",
            "ANSWER_VALUE",
            "ANSWER_TEXT",
            "RATIONALE_TEXT",
            "CITATIONS_JSON",
            "CONFIDENCE_SCORE",
            "ANSWER_STATUS",
            "STATUS",
            "EVALUATION_ID",
            "LLM_INVOCATION_ID",
            "RAW_RESPONSE_JSON",
            "ANSWER_JSON",
            "CREATED_AT",
            "UPDATED_AT",
        ):
            merged[column] = None
    allowed_col = "ANSWER_OPTIONS" if "ANSWER_OPTIONS" in merged.columns else "ALLOWED_VALUES"
    if allowed_col in merged.columns:
        merged["ALLOWED_VALUES_LIST"] = merged[allowed_col].apply(_normalize_allowed_values)
    else:
        merged["ALLOWED_VALUES_LIST"] = [[] for _ in range(len(merged))]
    merged["DISPLAY_ANSWER"] = merged.apply(get_answer_value, axis=1)
    return merged


def get_mfq_form_payload(session, claim_id: str) -> dict[str, Any]:
    started = perf_counter()
    available, missing_objects = _mfq_required_objects_available(session)
    if not available:
        logger.warning("get_mfq_form_payload_missing_objects claim_id=%s missing=%s", claim_id, missing_objects)
        return {
            "sections": pd.DataFrame(),
            "section_confidence": pd.DataFrame(),
            "confidence_summary": get_claim_confidence_summary(session, claim_id, None, {}, pd.DataFrame(), missing_objects),
            "missing_objects": missing_objects,
            "mfq_available": False,
        }

    sections_df = get_active_mfq_sections_and_questions(session)
    answers_cache = _session_claim_cache("mfq_answers_cache")
    if str(claim_id) in answers_cache:
        answers_df = answers_cache[str(claim_id)]
        logger.info("mfq_answers_cache_hit claim_id=%s rows=%d", claim_id, len(answers_df) if isinstance(answers_df, pd.DataFrame) else -1)
    else:
        answers_df = get_current_mfq_answers_by_claim_id(session, claim_id)
        answers_cache[str(claim_id)] = answers_df
    merged_sections = _merge_mfq_sections_answers(sections_df, answers_df)
    section_confidence = get_claim_section_confidence(session, claim_id, merged_sections)
    confidence_summary = get_claim_confidence_summary(session, claim_id, None, {}, merged_sections, [])
    logger.info("get_mfq_form_payload_ms=%d claim_id=%s questions=%d answers=%d", int((perf_counter() - started) * 1000), claim_id, len(merged_sections), len(answers_df))
    return {
        "sections": merged_sections,
        "answers": answers_df,
        "section_confidence": section_confidence,
        "confidence_summary": confidence_summary,
        "missing_objects": [],
        "mfq_available": True,
    }


def build_mfq_workspace_for_claim(session, claim_id: str) -> dict[str, Any]:
    form_cache = _session_claim_cache("mfq_form_cache")
    claim_key = str(claim_id)
    if claim_key in form_cache:
        logger.info("mfq_form_cache_hit claim_id=%s", claim_id)
        return form_cache[claim_key]
    started = perf_counter()
    payload = get_mfq_form_payload(session, claim_id)
    form_cache[claim_key] = payload
    logger.info("build_mfq_workspace_for_claim_ms=%d claim_id=%s questions=%d", int((perf_counter() - started) * 1000), claim_id, len(payload.get("sections", pd.DataFrame())))
    return payload


def _normalize_allowed_values(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(v) for v in raw]
    text = str(raw).strip()
    if not text:
        return []
    try:
        loaded = json.loads(text)
        if isinstance(loaded, list):
            return [str(v) for v in loaded]
        if isinstance(loaded, dict):
            for key in ("options", "values", "choices", "items"):
                values = loaded.get(key)
                if isinstance(values, list):
                    return [str(v) for v in values]
    except Exception:
        pass
    return [piece.strip() for piece in text.split(",") if piece.strip()]


def get_mfq_form_workspace(session, claim_id: str, defendant_id: str | None = None) -> pd.DataFrame:
    """Backward-compatible dataframe workspace built from the updated MFQ tables."""
    del defendant_id
    payload = get_mfq_form_payload(session, claim_id)
    return payload.get("sections", pd.DataFrame())


@st.cache_data(ttl=300, show_spinner=False)
def _get_status_values_cached(_session, cache_scope: str) -> list[str]:
    del cache_scope
    df = mfq_repository.get_status_values(_session)
    statuses = [str(v) for v in df["STATUS"].dropna().tolist()] if not df.empty else []
    return ["All", *statuses]


def get_status_values(session) -> list[str]:
    if _in_streamlit_runtime():
        return _get_status_values_cached(session, _claims_cache_scope(session))
    df = mfq_repository.get_status_values(session)
    statuses = [str(v) for v in df["STATUS"].dropna().tolist()] if not df.empty else []
    return ["All", *statuses]


def get_claim_review_workspace(session, claim_id: str) -> dict[str, Any]:
    started = perf_counter()
    claim_id_q = quote_sql(claim_id)
    missing_objects: list[str] = []

    t_detail = perf_counter()
    if _object_exists(session, DETAIL_VIEW):
        detail_df = claims_repository.get_claim_detail(session, claim_id)
    else:
        missing_objects.append(DETAIL_VIEW)
        detail_df = pd.DataFrame()
    logger.info("claim_workspace.detail_ms=%d claim_id=%s", int((perf_counter() - t_detail) * 1000), claim_id)
    defendant_df = claims_repository.get_claim_defendants(session, claim_id) if _object_exists(session, obj.MFQ_CLAIM_DEFENDANTS_TABLE) else pd.DataFrame()

    detail = detail_df.iloc[0].to_dict() if not detail_df.empty else None
    if detail is not None and _object_exists(session, obj.VW_MFQ_CLAIMS):
        status_df = claims_repository.get_claim_status_snapshot(session, claim_id)
        if not status_df.empty:
            status_snapshot = status_df.iloc[0].to_dict()
            for key, value in status_snapshot.items():
                current_value = detail.get(key)
                if current_value is None or (isinstance(current_value, float) and pd.isna(current_value)) or str(current_value).strip().lower() in {"", "nan", "none", "null"}:
                    detail[key] = value
    synopsis = defendant_df.iloc[0].to_dict() if not defendant_df.empty else {}
    if detail is not None and synopsis:
        for key in ("DEFENDANT_ID", "DEFENDANT_NAME", "DEFENDANT_SPECIALTY", "DEFENDANT_SPECIALITY", "SPECIALTY", "SPECIALITY"):
            current_value = detail.get(key)
            synopsis_value = synopsis.get(key)
            if current_value is None or (isinstance(current_value, float) and pd.isna(current_value)) or str(current_value).strip().lower() in {"", "nan", "none", "null"}:
                detail[key] = synopsis_value
    defendant_id = synopsis.get("DEFENDANT_ID") or (detail.get("DEFENDANT_ID") if detail else None)

    sections_df = pd.DataFrame()
    form_objects = [SECTIONS_TABLE, QUESTIONS_TABLE, ANSWERS_TABLE, QUESTION_CONFIDENCE_TABLE]
    if all(_object_exists(session, obj) for obj in form_objects):
        t_sections = perf_counter()
        sections_df = get_mfq_form_workspace(session, claim_id, defendant_id=str(defendant_id) if defendant_id else None)
        logger.info("claim_workspace.sections_ms=%d claim_id=%s", int((perf_counter() - t_sections) * 1000), claim_id)
    else:
        sections_df = _safe_read(
            session,
            FORM_VIEW,
            f"""
            SELECT
                SECTION_ID,
                SECTION_NAME,
                SECTION_ORDER,
                QUESTION_ID,
                PARENT_QUESTION_ID,
                QUESTION_ORDER,
                QUESTION_TEXT,
                ANSWER_TYPE,
                ANSWER_TEXT,
                CONFIDENCE_SCORE
            FROM {FORM_VIEW}
            WHERE CLAIM_ID = '{claim_id_q}'
            ORDER BY SECTION_ORDER, QUESTION_ORDER
            """,
            missing_objects,
        )

    summary_df = mfq_repository.get_claim_summaries(session, claim_id)
    docs_df = claims_repository.get_claim_documents(session, claim_id) if _object_exists(session, obj.MFQ_DOCUMENTS_TABLE) else pd.DataFrame()
    assignment_df = claims_repository.get_assignment_queue(session, claim_id) if _object_exists(session, obj.MFQ_ASSIGNMENT_QUEUE_VIEW) else pd.DataFrame()

    enquiries_df = claims_repository.get_status_history(session, claim_id) if _object_exists(session, obj.MFQ_STATUS_HISTORY_TABLE) else pd.DataFrame()

    confidence_summary = get_claim_confidence_summary(
        session=session,
        claim_id=claim_id,
        claim_detail=detail,
        synopsis=synopsis,
        sections_df=sections_df,
        missing_objects=missing_objects,
    )
    section_confidence = get_claim_section_confidence(session, claim_id, sections_df)

    summary_map: dict[str, str] = {}
    if not summary_df.empty:
        for _, row in summary_df.iterrows():
            summary_type = str(row.get("SUMMARY_TYPE", "")).strip().upper()
            if summary_type and summary_type not in summary_map:
                summary_map[summary_type] = str(row.get("SUMMARY_TEXT", "") or "")

    if not sections_df.empty and "ALLOWED_VALUES" in sections_df.columns:
        sections_df = sections_df.copy()
        sections_df["ALLOWED_VALUES_LIST"] = sections_df["ALLOWED_VALUES"].apply(_normalize_allowed_values)
    if not sections_df.empty:
        if "ALLOWED_VALUES_LIST" not in sections_df.columns:
            sections_df = sections_df.copy()
            sections_df["ALLOWED_VALUES_LIST"] = [[] for _ in range(len(sections_df))]
        sections_df["DISPLAY_ANSWER"] = sections_df.apply(get_answer_value, axis=1)

    used_objects = {
        DETAIL_VIEW,
        FORM_VIEW,
        SECTIONS_TABLE,
        QUESTIONS_TABLE,
        ANSWERS_TABLE,
        QUESTION_CONFIDENCE_TABLE,
        SECTION_CONFIDENCE_TABLE,
        "MFQ_CLAIMS_VW",
        "MFQ_CLAIM_DETAIL_VW",
        "MFQ_CLAIM_DEFENDANTS",
        "MFQ_RECORD_SUMMARY",
        "MFQ_MEDCRON_SUMMARY",
        "MFQ_LEGAL_MEMO",
        "MFQ_DOCUMENTS",
        "MFQ_ASSIGNMENT_QUEUE_VW",
        "MFQ_STATUS_HISTORY",
        LLM_EVAL_TABLE,
    }

    result = {
        "claim": detail,
        "sections": sections_df,
        "synopsis": synopsis,
        "section_confidence": section_confidence,
        "overall_confidence": confidence_summary.get("overall_confidence"),
        "confidence_summary": confidence_summary,
        "summaries": summary_map,
        "documents": docs_df,
        "assignment": assignment_df,
        "enquiries": enquiries_df,
        "missing_objects": sorted(set(missing_objects)),
        "used_objects": sorted(used_objects),
    }
    logger.info("get_claim_review_workspace_ms=%d claim_id=%s", int((perf_counter() - started) * 1000), claim_id)
    return result


def _normalize_confidence_score(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    score = float(value)
    return score * 100.0 if 0.0 <= score <= 1.0 else score


def _confidence_status_from_score(value: Any) -> str:
    score = _normalize_confidence_score(value)
    if score is None:
        return "Unknown"
    if score >= 90:
        return "High"
    if score >= 80:
        return "Moderate"
    return "Low"


def _parse_json_like(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    text = str(raw).strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return text


def extract_answer_json_value(raw: Any) -> Any:
    parsed = _parse_json_like(raw)
    if parsed is None:
        return None
    if isinstance(parsed, dict):
        for key in ("value", "answer", "selected", "text"):
            value = parsed.get(key)
            if value not in (None, ""):
                return value
        return None
    return parsed


def get_answer_value(row: pd.Series | dict[str, Any]) -> str:
    candidates = [
        row.get("REVIEWED_ANSWER"),
        row.get("ANSWER_VALUE"),
        row.get("ANSWER_TEXT"),
        extract_answer_json_value(row.get("ANSWER_JSON")),
        row.get("GENERATED_ANSWER"),
    ]
    value = ""
    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, float) and pd.isna(candidate):
            continue
        if str(candidate).strip() == "":
            continue
        value = candidate
        break
    parsed = _parse_json_like(value)
    if parsed is None:
        return ""
    if isinstance(parsed, list):
        return ", ".join([str(v).strip() for v in parsed if str(v).strip()])
    if isinstance(parsed, dict):
        return json.dumps(parsed)
    return str(parsed).strip()


def get_claim_section_confidence(session, claim_id: str, sections_df: pd.DataFrame) -> pd.DataFrame:
    if _object_exists(session, SECTION_CONFIDENCE_TABLE) and _object_exists(session, SECTIONS_TABLE):
        claim_id_q = quote_sql(claim_id)
        section_df = safe_collect_df(
            session,
            f"""
            SELECT
              s.SECTION_NAME,
              s.DISPLAY_ORDER AS SECTION_ORDER,
              sc.CONFIDENCE_SCORE
            FROM {SECTION_CONFIDENCE_TABLE} sc
            JOIN {SECTIONS_TABLE} s
              ON s.SECTION_ID = sc.SECTION_ID
            WHERE sc.CLAIM_ID = '{claim_id_q}'
            ORDER BY s.DISPLAY_ORDER, s.SECTION_NAME
            """,
        )
        if not section_df.empty:
            section_df["CONFIDENCE_SCORE_PCT"] = section_df["CONFIDENCE_SCORE"].apply(_normalize_confidence_score)
            section_df["CONFIDENCE_STATUS"] = section_df["CONFIDENCE_SCORE_PCT"].apply(_confidence_status_from_score)
            return section_df

    if sections_df.empty or "CONFIDENCE_SCORE" not in sections_df.columns:
        return pd.DataFrame()

    grouped = (
        sections_df.groupby(["SECTION_NAME", "SECTION_ORDER"], dropna=False)["CONFIDENCE_SCORE"]
        .mean()
        .reset_index()
        .sort_values(["SECTION_ORDER", "SECTION_NAME"])
    )
    grouped["CONFIDENCE_SCORE_PCT"] = grouped["CONFIDENCE_SCORE"].apply(_normalize_confidence_score)
    grouped["CONFIDENCE_STATUS"] = grouped["CONFIDENCE_SCORE_PCT"].apply(_confidence_status_from_score)
    return grouped


def get_claim_confidence_summary(
    session,
    claim_id: str,
    claim_detail: dict[str, Any] | None,
    synopsis: dict[str, Any],
    sections_df: pd.DataFrame,
    missing_objects: list[str],
) -> dict[str, Any]:
    overall_confidence = None
    if claim_detail and claim_detail.get("AI_CONFIDENCE") is not None:
        overall_confidence = _normalize_confidence_score(claim_detail.get("AI_CONFIDENCE"))
    elif not sections_df.empty and sections_df["CONFIDENCE_SCORE"].notna().any():
        overall_confidence = _normalize_confidence_score(sections_df["CONFIDENCE_SCORE"].dropna().mean())

    recommendation = None
    explanation = None
    defendant_id = synopsis.get("DEFENDANT_ID")
    if defendant_id and _object_exists(session, LLM_EVAL_TABLE):
        llm_eval_df = mfq_repository.get_llm_evaluation(session, str(defendant_id))
        if not llm_eval_df.empty:
            needs_human_review = llm_eval_df.iloc[0].get("NEEDS_HUMAN_REVIEW")
            if needs_human_review is True:
                recommendation = "Faculty Review Recommended"
            elif needs_human_review is False:
                recommendation = "No Faculty Review Needed"
    elif defendant_id:
        missing_objects.append(LLM_EVAL_TABLE)

    if recommendation is None:
        status = _confidence_status_from_score(overall_confidence)
        recommendation = "No Faculty Review Needed" if status == "High" else "Faculty Review Recommended"

    if overall_confidence is None:
        explanation = "AI confidence data is not available for this claim."
    elif overall_confidence >= 90:
        explanation = "AI extraction confidence is high across sections and appears reliable for direct processing."
    elif overall_confidence >= 80:
        explanation = "AI extraction confidence is moderate and a targeted faculty review is recommended."
    else:
        explanation = "AI extraction confidence is low and detailed faculty review is required."

    return {
        "claim_id": claim_id,
        "overall_confidence": overall_confidence,
        "confidence_status": _confidence_status_from_score(overall_confidence),
        "recommendation": recommendation,
        "explanation": explanation,
    }


def update_claim_status(session, claim_id: str, new_status: str, assigned_to: str | None = None) -> None:
    claims_repository.update_claim_status(session, claim_id, new_status)
    if assigned_to:
        claims_repository.touch_assignment_for_username(session, claim_id, assigned_to)
    if _in_streamlit_runtime():
        clear_claim_read_caches()


@st.cache_data(ttl=300, show_spinner=False)
def get_assignable_faculty(_session) -> list[dict[str, str]]:
    if not _object_exists(_session, "MFQ_USERS"):
        return []

    has_role_tables = _object_exists(_session, "MFQ_USER_ROLES") and _object_exists(_session, "MFQ_ROLES")
    if has_role_tables:
        df = safe_collect_df(
            _session,
            """
            SELECT DISTINCT
              u.USER_ID,
              u.USERNAME,
              COALESCE(NULLIF(u.DISPLAY_NAME, ''), u.USERNAME) AS DISPLAY_NAME
            FROM MFQ_USERS u
            JOIN MFQ_USER_ROLES ur
              ON ur.USER_ID = u.USER_ID
             AND COALESCE(ur.IS_ACTIVE, TRUE) = TRUE
            JOIN MFQ_ROLES r
              ON r.ROLE_ID = ur.ROLE_ID
             AND COALESCE(r.IS_ACTIVE, TRUE) = TRUE
            WHERE COALESCE(u.IS_ACTIVE, TRUE) = TRUE
              AND (
                UPPER(COALESCE(r.ROLE_NAME, '')) = 'MEDICAL FACULTY'
                OR UPPER(COALESCE(r.ROLE_CODE, '')) IN ('MEDICAL_FACULTY', 'MEDICAL FACULTY')
              )
            ORDER BY DISPLAY_NAME
            """,
        )
    else:
        df = safe_collect_df(
            _session,
            """
            SELECT
              USER_ID,
              USERNAME,
              COALESCE(NULLIF(DISPLAY_NAME, ''), USERNAME) AS DISPLAY_NAME
            FROM MFQ_USERS
            WHERE COALESCE(IS_ACTIVE, TRUE) = TRUE
            ORDER BY DISPLAY_NAME
            """,
        )

    if df.empty:
        return []
    return [
        {
            "USER_ID": str(row.get("USER_ID", "") or ""),
            "USERNAME": str(row.get("USERNAME", "") or ""),
            "DISPLAY_NAME": str(row.get("DISPLAY_NAME", "") or ""),
        }
        for _, row in df.iterrows()
        if str(row.get("USER_ID", "") or "").strip()
    ]


def _save_assignment_placeholder(*, claim_id: str, faculty_user_id: str, section_ids: list[str], assigned_by_username: str) -> None:
    # TODO: Replace this placeholder with the production assignment API/repository call
    # when backend assignment persistence service is available in this environment.
    _ = (claim_id, faculty_user_id, section_ids, assigned_by_username)


def save_claim_assignment(
    session,
    claim_id: str,
    faculty_user_id: str,
    section_ids: list[str],
    assigned_by_username: str,
) -> tuple[bool, str]:
    assignment_tables_exist = _object_exists(session, "MFQ_ASSIGNMENTS") and _object_exists(session, "MFQ_ASSIGNMENT_SECTIONS")
    if not assignment_tables_exist:
        _save_assignment_placeholder(
            claim_id=claim_id,
            faculty_user_id=faculty_user_id,
            section_ids=section_ids,
            assigned_by_username=assigned_by_username,
        )
        return False, "Assignment persistence tables are unavailable in this environment."

    assigned_user_df = assignment_repository.get_assignment_username(session, faculty_user_id)
    assigned_username = (
        str(assigned_user_df.iloc[0].get("USERNAME", "") or "").strip()
        if not assigned_user_df.empty
        else ""
    )
    assignment_repository.insert_assignment(session, claim_id, faculty_user_id, assigned_by_username)

    assignment_id_df = assignment_repository.get_latest_assignment_id(session, claim_id, faculty_user_id)
    if assignment_id_df.empty:
        return False, "Could not resolve assignment identifier after save."

    assignment_repository.insert_assignment_sections(
        session, str(assignment_id_df.iloc[0]["ASSIGNMENT_ID"]), claim_id, faculty_user_id, section_ids
    )

    claim_cols = _table_columns(session, obj.MFQ_CLAIMS_TABLE)
    assignment_repository.update_claim_for_assignment(session, claim_id, assigned_username, claim_cols)

    return True, "Claim assigned successfully."


def save_section_answer(
    session,
    answer_id: str,
    answer_text: str,
    claim_id: str | None = None,
    defendant_id: str | None = None,
    question_id: str | None = None,
) -> None:
    if not (claim_id and question_id):
        return

    cols = _table_columns(session, ANSWERS_TABLE)
    claim_q = quote_sql(claim_id)
    question_q = quote_sql(question_id)
    defendant_q = quote_sql(defendant_id) if defendant_id else ""
    answer_q = quote_sql(answer_text)

    has_last_updated = "LAST_UPDATED_TS" in cols
    has_updated_at = "UPDATED_AT" in cols
    has_updated_by = "UPDATED_BY" in cols
    has_created_ts = "CREATED_TS" in cols
    has_created_at = "CREATED_AT" in cols

    timestamp_updates = []
    if has_last_updated:
        timestamp_updates.append("LAST_UPDATED_TS = CURRENT_TIMESTAMP()")
    if has_updated_at:
        timestamp_updates.append("UPDATED_AT = CURRENT_TIMESTAMP()")
    if has_updated_by:
        timestamp_updates.append("UPDATED_BY = CURRENT_USER()")
    if not timestamp_updates:
        timestamp_updates.append("IS_CURRENT = IS_CURRENT")

    defendant_match = ""
    defendant_insert_col = ""
    defendant_insert_val = ""
    if "DEFENDANT_ID" in cols and defendant_id:
        defendant_match = f" AND DEFENDANT_ID = '{defendant_q}'"
        defendant_insert_col = ", DEFENDANT_ID"
        defendant_insert_val = f", '{defendant_q}'"

    session.sql(
        f"""
        UPDATE {ANSWERS_TABLE}
        SET IS_CURRENT = FALSE,
            {', '.join(timestamp_updates)}
        WHERE CLAIM_ID = '{claim_q}'
          AND QUESTION_ID = '{question_q}'
          {defendant_match}
          AND IS_CURRENT = TRUE
        """
    ).collect()

    insert_columns = ["ANSWER_ID", "CLAIM_ID", "QUESTION_ID", "ANSWER_TEXT", "STATUS", "IS_CURRENT"]
    insert_values = ["CONCAT('ANS-', REPLACE(UUID_STRING(), '-', ''))", f"'{claim_q}'", f"'{question_q}'", f"'{answer_q}'", "'REVIEWED'", "TRUE"]

    if defendant_insert_col:
        insert_columns.insert(2, "DEFENDANT_ID")
        insert_values.insert(2, defendant_insert_val.lstrip(", "))

    if "ANSWER_JSON" in cols:
        insert_columns.append("ANSWER_JSON")
        insert_values.append(f"OBJECT_CONSTRUCT('value', '{answer_q}')")
    if has_created_ts:
        insert_columns.append("CREATED_TS")
        insert_values.append("CURRENT_TIMESTAMP()")
    if "LAST_UPDATED_TS" in cols:
        insert_columns.append("LAST_UPDATED_TS")
        insert_values.append("CURRENT_TIMESTAMP()")
    if has_created_at:
        insert_columns.append("CREATED_AT")
        insert_values.append("CURRENT_TIMESTAMP()")
    if has_updated_at:
        insert_columns.append("UPDATED_AT")
        insert_values.append("CURRENT_TIMESTAMP()")
    if has_updated_by:
        insert_columns.append("UPDATED_BY")
        insert_values.append("CURRENT_USER()")

    session.sql(
        f"""
        INSERT INTO {ANSWERS_TABLE} ({', '.join(insert_columns)})
        SELECT {', '.join(insert_values)}
        """
    ).collect()


def save_mfq_answer(
    session,
    claim_id: str,
    defendant_id: str | None,
    question_id: str,
    answer_value: Any,
    user_id: str,
    section_id: str | None = None,
) -> None:
    if not (claim_id and question_id):
        return

    cols = _table_columns(session, ANSWERS_TABLE)
    claim_q = quote_sql(claim_id)
    question_q = quote_sql(question_id)
    section_q = quote_sql(section_id) if section_id else ""
    defendant_q = quote_sql(defendant_id) if defendant_id else ""
    user_q = quote_sql(user_id)

    if isinstance(answer_value, list):
        answer_text = ", ".join([str(v) for v in answer_value])
    elif isinstance(answer_value, dict):
        answer_text = json.dumps(answer_value)
    elif answer_value is None:
        answer_text = ""
    else:
        answer_text = str(answer_value)
    answer_text_q = quote_sql(answer_text)
    answer_json_q = quote_sql(json.dumps({"value": answer_value}))

    has_defendant = "DEFENDANT_ID" in cols
    has_section = "SECTION_ID" in cols
    has_answer_value = "ANSWER_VALUE" in cols
    has_answer_json = "ANSWER_JSON" in cols
    has_raw_response_json = "RAW_RESPONSE_JSON" in cols
    status_column = "ANSWER_STATUS" if "ANSWER_STATUS" in cols else "STATUS" if "STATUS" in cols else ""
    has_status = bool(status_column)
    has_created_ts = "CREATED_TS" in cols
    has_last_updated = "LAST_UPDATED_TS" in cols
    has_created_at = "CREATED_AT" in cols
    has_updated_at = "UPDATED_AT" in cols
    has_updated_by = "UPDATED_BY" in cols
    has_user_reviewed = "USER_REVIEWED" in cols

    src_columns = [f"'{claim_q}' AS CLAIM_ID", f"'{question_q}' AS QUESTION_ID", f"'{answer_text_q}' AS ANSWER_TEXT"]
    if has_section and section_id:
        src_columns.append(f"'{section_q}' AS SECTION_ID")
    if has_defendant and defendant_id:
        src_columns.append(f"'{defendant_q}' AS DEFENDANT_ID")

    merge_on = "tgt.CLAIM_ID = src.CLAIM_ID AND tgt.QUESTION_ID = src.QUESTION_ID AND tgt.IS_CURRENT = TRUE"
    if has_defendant and defendant_id:
        merge_on += " AND tgt.DEFENDANT_ID = src.DEFENDANT_ID"

    update_set = ["tgt.ANSWER_TEXT = src.ANSWER_TEXT"]
    if has_section and section_id:
        update_set.append("tgt.SECTION_ID = src.SECTION_ID")
    if has_answer_value:
        update_set.append("tgt.ANSWER_VALUE = src.ANSWER_TEXT")
    if has_answer_json:
        update_set.append(f"tgt.ANSWER_JSON = PARSE_JSON('{answer_json_q}')")
    if has_raw_response_json:
        update_set.append(f"tgt.RAW_RESPONSE_JSON = PARSE_JSON('{answer_json_q}')")
    if has_status:
        update_set.append(f"tgt.{status_column} = 'USER_REVIEWED'")
    if has_user_reviewed:
        update_set.append("tgt.USER_REVIEWED = TRUE")
    if has_last_updated:
        update_set.append("tgt.LAST_UPDATED_TS = CURRENT_TIMESTAMP()")
    if has_updated_at:
        update_set.append("tgt.UPDATED_AT = CURRENT_TIMESTAMP()")
    if has_updated_by:
        update_set.append(f"tgt.UPDATED_BY = '{user_q}'")

    insert_columns = ["ANSWER_ID", "CLAIM_ID", "QUESTION_ID", "ANSWER_TEXT", "IS_CURRENT"]
    insert_values = [
        "CONCAT('ANS-', REPLACE(UUID_STRING(), '-', ''))",
        "src.CLAIM_ID",
        "src.QUESTION_ID",
        "src.ANSWER_TEXT",
        "TRUE",
    ]
    if has_section and section_id:
        insert_columns.append("SECTION_ID")
        insert_values.append("src.SECTION_ID")
    if has_defendant and defendant_id:
        insert_columns.insert(2, "DEFENDANT_ID")
        insert_values.insert(2, "src.DEFENDANT_ID")
    if has_answer_value:
        insert_columns.append("ANSWER_VALUE")
        insert_values.append("src.ANSWER_TEXT")
    if has_answer_json:
        insert_columns.append("ANSWER_JSON")
        insert_values.append(f"PARSE_JSON('{answer_json_q}')")
    if has_raw_response_json:
        insert_columns.append("RAW_RESPONSE_JSON")
        insert_values.append(f"PARSE_JSON('{answer_json_q}')")
    if has_status:
        insert_columns.append(status_column)
        insert_values.append("'USER_REVIEWED'")
    if has_user_reviewed:
        insert_columns.append("USER_REVIEWED")
        insert_values.append("TRUE")
    if has_created_ts:
        insert_columns.append("CREATED_TS")
        insert_values.append("CURRENT_TIMESTAMP()")
    if has_last_updated:
        insert_columns.append("LAST_UPDATED_TS")
        insert_values.append("CURRENT_TIMESTAMP()")
    if has_created_at:
        insert_columns.append("CREATED_AT")
        insert_values.append("CURRENT_TIMESTAMP()")
    if has_updated_at:
        insert_columns.append("UPDATED_AT")
        insert_values.append("CURRENT_TIMESTAMP()")
    if has_updated_by:
        insert_columns.append("UPDATED_BY")
        insert_values.append(f"'{user_q}'")

    session.sql(
        f"""
        MERGE INTO {ANSWERS_TABLE} AS tgt
        USING (
          SELECT {', '.join(src_columns)}
        ) AS src
        ON {merge_on}
        WHEN MATCHED THEN
          UPDATE SET {', '.join(update_set)}
        WHEN NOT MATCHED THEN
          INSERT ({', '.join(insert_columns)})
          VALUES ({', '.join(insert_values)})
        """
    ).collect()


def get_editable_section_ids_for_user(session, claim_id: str, username: str) -> set[str] | None:
    # Keep all sections editable when no assignment section table exists.
    claim_q = quote_sql(claim_id)
    user_q = quote_sql(username)
    if not (_object_exists(session, obj.MFQ_ASSIGNMENT_SECTIONS_TABLE) and _object_exists(session, obj.MFQ_USERS_TABLE)):
        return set()

    df = assignment_repository.get_editable_section_ids(session, claim_id, username)
    if df.empty:
        return set()
    return {str(v) for v in df["SECTION_ID"].dropna().tolist()}
