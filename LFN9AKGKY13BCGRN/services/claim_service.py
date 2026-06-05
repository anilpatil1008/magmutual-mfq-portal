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
from repositories import assignment_repository, claims_repository, faculty_repository, mfq_repository, user_repository
from services.snowflake_service import quote_sql, safe_collect_df
from utils.claim_lifecycle import classify_claim_bucket


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
CLAIMS_SEARCHABLE_COLUMNS = (
    "CLAIM_ID",
    "FILE_NUMBER",
    "PATIENT_DEFENDANT",
    "DEFENDANT_NAME",
    "MFQ_STATUS",
    "WORKFLOW_STATUS",
    "PRIORITY",
    "CLAIM_STATUS",
    "CLAIM_TYPE",
    "DATE_REQUESTED",
    "AI_CONFIDENCE",
)


def _claims_cache_scope() -> str:
    """Key cached claims by app role/context without hashing the Snowflake session."""
    return str(st.session_state.get("selected_sf_role") or "default")


def _in_streamlit_runtime() -> bool:
    return get_script_run_ctx(suppress_warning=True) is not None


def _normalize_search_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.dt.strftime("%Y-%m-%d").fillna("").str.lower()
    return series.fillna("").astype(str).str.lower()


def add_claims_search_index(df: pd.DataFrame, search_columns: tuple[str, ...] = CLAIMS_SEARCHABLE_COLUMNS) -> pd.DataFrame:
    """Copy a claims dataframe and precompute one lowercase string search index per row."""
    indexed = df.copy()
    if indexed.empty:
        indexed[CLAIMS_SEARCH_INDEX_COLUMN] = pd.Series(dtype=str)
        return indexed

    normalized_columns = [column for column in search_columns if column in indexed.columns]
    if not normalized_columns:
        indexed[CLAIMS_SEARCH_INDEX_COLUMN] = ""
        return indexed

    search_parts = [_normalize_search_series(indexed[column]) for column in normalized_columns]
    indexed[CLAIMS_SEARCH_INDEX_COLUMN] = pd.concat(search_parts, axis=1).agg(" ".join, axis=1)
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


def _object_exists(session, object_name: str) -> bool:
    object_q = quote_sql(object_name.upper())
    sql = f"""
      SELECT 1 AS FOUND
      FROM INFORMATION_SCHEMA.TABLES
      WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
        AND TABLE_NAME = '{object_q}'
      UNION ALL
      SELECT 1 AS FOUND
      FROM INFORMATION_SCHEMA.VIEWS
      WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
        AND TABLE_NAME = '{object_q}'
      LIMIT 1
    """
    return claims_repository.object_exists(session, object_name)


def _table_columns(session, table_name: str) -> set[str]:
    if not _object_exists(session, table_name):
        return set()
    table_q = quote_sql(table_name.upper())
    cols_df = safe_collect_df(
        session,
        f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
          AND TABLE_NAME = '{table_q}'
        """,
    )
    if cols_df.empty:
        return set()
    return {str(col).upper() for col in cols_df["COLUMN_NAME"].dropna().tolist()}


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
        _load_claims_queue_cached(session, _claims_cache_scope())
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


def get_filtered_recent_claims(session, filters: dict | None, page: int, page_size: int) -> pd.DataFrame:
    return claims_repository.get_filtered_recent_claims(session, filters, page, page_size)


def get_cached_recent_claims(session) -> pd.DataFrame:
    """Load recent claims once per cache scope for fast in-memory dashboard filtering."""
    if _in_streamlit_runtime():
        return _load_recent_claims_cached(session, _claims_cache_scope())
    return add_claims_search_index(claims_repository.get_recent_claims_dataset(session))


def _local_filter_values(df: pd.DataFrame, column_name: str, values: list[str], all_labels: set[str]) -> pd.DataFrame:
    filtered_values = [str(value).strip() for value in values if str(value).strip() and value not in all_labels]
    if not filtered_values or column_name not in df.columns:
        return df
    selected = {value.upper() for value in filtered_values}
    return df[df[column_name].fillna("").astype(str).str.upper().isin(selected)]


def _local_dashboard_filters(df: pd.DataFrame, filters: dict | None) -> pd.DataFrame:
    filters = filters or {}
    scoped = df.copy()
    scoped = _local_filter_values(scoped, "MFQ_STATUS", _coerce_filter_values(filters.get("selected_statuses")), {"All Statuses"})
    scoped = _local_filter_values(scoped, "PRIORITY", _coerce_filter_values(filters.get("selected_priorities")), {"All Priorities"})
    scoped = _local_filter_values(scoped, "CLAIM_TYPE", _coerce_filter_values(filters.get("selected_claim_types")), {"All Claim Types"})

    confidence_buckets = [value for value in _coerce_filter_values(filters.get("selected_ai_confidence_buckets")) if value != "All Scores"]
    if confidence_buckets and "AI_CONFIDENCE" in scoped.columns:
        confidence = pd.to_numeric(scoped["AI_CONFIDENCE"], errors="coerce")
        confidence_mask = pd.Series(False, index=scoped.index)
        if "High" in confidence_buckets:
            confidence_mask = confidence_mask | (confidence >= 90)
        if "Medium" in confidence_buckets:
            confidence_mask = confidence_mask | ((confidence >= 80) & (confidence < 90))
        if "Low" in confidence_buckets:
            confidence_mask = confidence_mask | (confidence < 80)
        scoped = scoped[confidence_mask]

    if "DATE_REQUESTED" in scoped.columns:
        requested_dates = pd.to_datetime(scoped["DATE_REQUESTED"], errors="coerce").dt.date
        date_requested_from = filters.get("date_requested_from")
        if date_requested_from is not None:
            scoped = scoped[requested_dates >= date_requested_from]
            requested_dates = requested_dates.loc[scoped.index]
        date_requested_to = filters.get("date_requested_to")
        if date_requested_to is not None:
            scoped = scoped[requested_dates <= date_requested_to]

    claim_bucket = str(filters.get("claim_bucket") or "").strip().lower()
    if claim_bucket in {"ongoing", "history"}:
        bucket_values = scoped.apply(classify_claim_bucket, axis=1)
        scoped = scoped[bucket_values == claim_bucket]

    return filter_claims_by_search(scoped, str(filters.get("search_text") or ""))


def get_filtered_recent_claims_local(claims: pd.DataFrame, filters: dict | None, page: int, page_size: int) -> pd.DataFrame:
    scoped = _local_dashboard_filters(claims, filters)
    offset = max(0, (max(1, int(page)) - 1) * max(1, int(page_size)))
    return scoped.iloc[offset : offset + max(1, int(page_size))].copy()


def get_filtered_claims_count_local(claims: pd.DataFrame, filters: dict | None) -> int:
    return len(_local_dashboard_filters(claims, filters))


def get_filtered_claims_count(session, filters: dict | None) -> int:
    return claims_repository.get_filtered_claims_count(session, filters)


def get_available_claim_statuses(session) -> list[str]:
    return claims_repository.get_available_claim_statuses(session)


def get_available_claim_types(session) -> list[str]:
    return claims_repository.get_available_claim_types(session)


def get_claim_details(session, claim_id: str) -> dict[str, Any] | None:
    df = claims_repository.get_claim_detail(session, claim_id)
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def get_mfq_form_workspace(session, claim_id: str, defendant_id: str | None = None) -> pd.DataFrame:
    claim_id_q = quote_sql(claim_id)
    answer_cols = _table_columns(session, ANSWERS_TABLE)
    question_conf_cols = _table_columns(session, QUESTION_CONFIDENCE_TABLE)

    answer_value_expr = "a.ANSWER_VALUE" if "ANSWER_VALUE" in answer_cols else "NULL"
    generated_answer_expr = "a.GENERATED_ANSWER" if "GENERATED_ANSWER" in answer_cols else "NULL"
    reviewed_answer_expr = "a.REVIEWED_ANSWER" if "REVIEWED_ANSWER" in answer_cols else "NULL"

    qc_level_expr = "qc.CONFIDENCE_LEVEL" if "CONFIDENCE_LEVEL" in question_conf_cols else "NULL"
    qc_reason_expr = "qc.CONFIDENCE_REASON" if "CONFIDENCE_REASON" in question_conf_cols else "NULL"

    question_key_join_predicates = ["a.QUESTION_ID = q.QUESTION_ID"]
    if "QUESTION_KEY" in answer_cols:
        question_key_join_predicates.append("a.QUESTION_KEY = q.QUESTION_KEY")
    if "FIELD_NAME" in answer_cols:
        question_key_join_predicates.append("a.FIELD_NAME = q.QUESTION_KEY")
    if "PDF_FIELD_NAME" in answer_cols:
        question_key_join_predicates.append("a.PDF_FIELD_NAME = q.QUESTION_KEY")
    question_join_predicate = " OR ".join(question_key_join_predicates)

    claim_join_predicates = [f"a.CLAIM_ID = '{claim_id_q}'"]
    if "FILE_NO" in answer_cols:
        claim_join_predicates.append(f"TRIM(a.FILE_NO) = '{claim_id_q}'")
    if "FILE_NUMBER" in answer_cols:
        claim_join_predicates.append(f"TRIM(a.FILE_NUMBER) = '{claim_id_q}'")
    answer_claim_join_predicate = " OR ".join(claim_join_predicates)

    sql = f"""
      SELECT
          s.SECTION_ID,
          s.SECTION_KEY,
          s.SECTION_NAME,
          s.DISPLAY_ORDER AS SECTION_ORDER,
          q.QUESTION_ID,
          q.QUESTION_KEY,
          q.PARENT_QUESTION_ID,
          q.DISPLAY_ORDER AS QUESTION_ORDER,
          q.QUESTION_TEXT,
          q.ANSWER_TYPE,
          q.ALLOWED_VALUES,
          q.VISIBILITY_RULE,
          a.ANSWER_ID,
          a.CLAIM_ID,
          a.DEFENDANT_ID,
          a.ANSWER_TEXT,
          a.ANSWER_JSON,
          {answer_value_expr} AS ANSWER_VALUE,
          {generated_answer_expr} AS GENERATED_ANSWER,
          {reviewed_answer_expr} AS REVIEWED_ANSWER,
          a.CONFIDENCE_SCORE,
          a.STATUS AS ANSWER_STATUS,
          a.IS_CURRENT,
          {qc_level_expr} AS CONFIDENCE_LEVEL,
          {qc_reason_expr} AS CONFIDENCE_REASON
      FROM {SECTIONS_TABLE} s
      JOIN {QUESTIONS_TABLE} q
          ON q.SECTION_ID = s.SECTION_ID
         AND q.FORM_KEY = s.FORM_KEY
      LEFT JOIN {ANSWERS_TABLE} a
          ON ({question_join_predicate})
         AND ({answer_claim_join_predicate})
         AND a.IS_CURRENT = TRUE
      LEFT JOIN {QUESTION_CONFIDENCE_TABLE} qc
          ON qc.QUESTION_ID = q.QUESTION_ID
         AND qc.CLAIM_ID = '{claim_id_q}'
      WHERE s.FORM_KEY = 'MFQ_V1'
        AND s.IS_ACTIVE = TRUE
        AND q.IS_ACTIVE = TRUE
        AND q.IS_CURRENT = TRUE
      ORDER BY s.DISPLAY_ORDER, q.DISPLAY_ORDER
    """
    return safe_collect_df(session, sql)


@st.cache_data(ttl=300, show_spinner=False)
def _get_status_values_cached(_session, cache_scope: str) -> list[str]:
    del cache_scope
    df = mfq_repository.get_status_values(_session)
    statuses = [str(v) for v in df["STATUS"].dropna().tolist()] if not df.empty else []
    return ["All", *statuses]


def get_status_values(session) -> list[str]:
    if _in_streamlit_runtime():
        return _get_status_values_cached(session, _claims_cache_scope())
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
            SELECT *
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

        def _normalize_allowed(raw: Any) -> list[str]:
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
            except Exception:
                pass
            return [piece.strip() for piece in text.split(",") if piece.strip()]

        sections_df = sections_df.copy()
        sections_df["ALLOWED_VALUES_LIST"] = sections_df["ALLOWED_VALUES"].apply(_normalize_allowed)
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
) -> None:
    if not (claim_id and question_id):
        return

    cols = _table_columns(session, ANSWERS_TABLE)
    claim_q = quote_sql(claim_id)
    question_q = quote_sql(question_id)
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
    has_answer_json = "ANSWER_JSON" in cols
    has_status = "STATUS" in cols
    has_created_ts = "CREATED_TS" in cols
    has_last_updated = "LAST_UPDATED_TS" in cols
    has_created_at = "CREATED_AT" in cols
    has_updated_at = "UPDATED_AT" in cols
    has_updated_by = "UPDATED_BY" in cols
    has_user_reviewed = "USER_REVIEWED" in cols

    src_columns = [f"'{claim_q}' AS CLAIM_ID", f"'{question_q}' AS QUESTION_ID", f"'{answer_text_q}' AS ANSWER_TEXT"]
    if has_defendant and defendant_id:
        src_columns.append(f"'{defendant_q}' AS DEFENDANT_ID")

    merge_on = "tgt.CLAIM_ID = src.CLAIM_ID AND tgt.QUESTION_ID = src.QUESTION_ID AND tgt.IS_CURRENT = TRUE"
    if has_defendant and defendant_id:
        merge_on += " AND tgt.DEFENDANT_ID = src.DEFENDANT_ID"

    update_set = ["tgt.ANSWER_TEXT = src.ANSWER_TEXT"]
    if has_answer_json:
        update_set.append(f"tgt.ANSWER_JSON = PARSE_JSON('{answer_json_q}')")
    if has_status:
        update_set.append("tgt.STATUS = 'USER_REVIEWED'")
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
    if has_defendant and defendant_id:
        insert_columns.insert(2, "DEFENDANT_ID")
        insert_values.insert(2, "src.DEFENDANT_ID")
    if has_answer_json:
        insert_columns.append("ANSWER_JSON")
        insert_values.append(f"PARSE_JSON('{answer_json_q}')")
    if has_status:
        insert_columns.append("STATUS")
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
