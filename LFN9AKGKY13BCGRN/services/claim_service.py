from __future__ import annotations

import json
from typing import Any

import pandas as pd

from services.snowflake_service import quote_sql, safe_collect_df


CLAIMS_VIEW = "MFQ_RECENT_CLAIMS_VW"
DETAIL_VIEW = "MFQ_CLAIM_DETAIL_VW"
FORM_VIEW = "MFQ_FORM_WORKSPACE_VW"
LLM_EVAL_TABLE = "LLM_EVALUATION"


def _apply_rbac(df: pd.DataFrame, app_role: str, username: str) -> pd.DataFrame:
    if df.empty or app_role in {"Admin", "Executive"}:
        return df
    if app_role in {"Claims Analyst", "Advice Team"}:
        return df
    if app_role == "Medical Faculty":
        return df[df["ASSIGNED_TO"].fillna("").str.upper() == username.upper()].copy()
    return df.head(0)


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
    return not safe_collect_df(session, sql).empty


def _safe_read(session, object_name: str, sql: str, missing_objects: list[str]) -> pd.DataFrame:
    if not _object_exists(session, object_name):
        missing_objects.append(object_name)
        return pd.DataFrame()
    return safe_collect_df(session, sql)


def get_claims_queue(session, app_role: str, username: str, search_text: str = "", status_filter: str = "All") -> pd.DataFrame:
    df = safe_collect_df(session, f"SELECT * FROM {CLAIMS_VIEW}")
    if df.empty:
        return df

    scoped = _apply_rbac(df, app_role, username)
    if search_text.strip():
        needle = search_text.strip().lower()
        scoped = scoped[
            scoped["CLAIM_ID"].astype(str).str.lower().str.contains(needle)
            | scoped["PATIENT_NAME"].astype(str).str.lower().str.contains(needle)
            | scoped["DEFENDANT_NAME"].astype(str).str.lower().str.contains(needle)
            | scoped["FILE_NUMBER"].astype(str).str.lower().str.contains(needle)
            | scoped["STATUS"].astype(str).str.lower().str.contains(needle)
            | scoped["PRIORITY"].astype(str).str.lower().str.contains(needle)
        ]

    if status_filter != "All":
        scoped = scoped[scoped["STATUS"] == status_filter]

    return scoped.sort_values("LAST_UPDATED_TS", ascending=False)


def get_claim_details(session, claim_id: str) -> dict[str, Any] | None:
    claim_id_q = quote_sql(claim_id)
    df = safe_collect_df(session, f"SELECT * FROM {DETAIL_VIEW} WHERE CLAIM_ID = '{claim_id_q}'")
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def get_claim_sections(session, claim_id: str) -> pd.DataFrame:
    claim_id_q = quote_sql(claim_id)
    sql = f"""
      SELECT *
      FROM {FORM_VIEW}
      WHERE CLAIM_ID = '{claim_id_q}'
      ORDER BY SECTION_ORDER, QUESTION_ORDER
    """
    df = safe_collect_df(session, sql)
    if not df.empty and "ANSWER_TEXT" in df.columns:
        df["ANSWER_TEXT"] = df["ANSWER_TEXT"].fillna("")
    return df


def get_status_values(session) -> list[str]:
    df = safe_collect_df(session, f"SELECT DISTINCT STATUS FROM {CLAIMS_VIEW} ORDER BY STATUS")
    statuses = [str(v) for v in df["STATUS"].dropna().tolist()] if not df.empty else []
    return ["All", *statuses]


def get_claim_review_workspace(session, claim_id: str) -> dict[str, Any]:
    claim_id_q = quote_sql(claim_id)
    missing_objects: list[str] = []

    detail_df = _safe_read(
        session,
        DETAIL_VIEW,
        f"SELECT * FROM {DETAIL_VIEW} WHERE CLAIM_ID = '{claim_id_q}'",
        missing_objects,
    )
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
    defendant_df = _safe_read(
        session,
        "MFQ_CLAIM_DEFENDANTS",
        f"SELECT * FROM MFQ_CLAIM_DEFENDANTS WHERE CLAIM_ID = '{claim_id_q}'",
        missing_objects,
    )
    summary_df = _safe_read(
        session,
        "MFQ_RECORD_SUMMARY",
        f"""
        SELECT 'RECORD_SUMMARY' AS SUMMARY_TYPE, SUMMARY_TEXT, GENERATED_TS FROM MFQ_RECORD_SUMMARY WHERE CLAIM_ID = '{claim_id_q}'
        UNION ALL
        SELECT 'MEDCRON' AS SUMMARY_TYPE, SUMMARY_TEXT, GENERATED_TS FROM MFQ_MEDCRON_SUMMARY WHERE CLAIM_ID = '{claim_id_q}'
        UNION ALL
        SELECT 'LEGAL_MEMO' AS SUMMARY_TYPE, SUMMARY_TEXT, GENERATED_TS FROM MFQ_LEGAL_MEMO WHERE CLAIM_ID = '{claim_id_q}'
        ORDER BY GENERATED_TS DESC
        """,
        missing_objects,
    )
    docs_df = _safe_read(
        session,
        "MFQ_DOCUMENTS",
        f"SELECT * FROM MFQ_DOCUMENTS WHERE CLAIM_ID = '{claim_id_q}' ORDER BY CREATED_TS DESC",
        missing_objects,
    )
    assignment_df = _safe_read(
        session,
        "MFQ_ASSIGNMENT_QUEUE_VW",
        f"SELECT * FROM MFQ_ASSIGNMENT_QUEUE_VW WHERE CLAIM_ID = '{claim_id_q}' ORDER BY ASSIGNED_AT DESC",
        missing_objects,
    )

    enquiries_df = _safe_read(
        session,
        "MFQ_STATUS_HISTORY",
        f"SELECT * FROM MFQ_STATUS_HISTORY WHERE CLAIM_ID = '{claim_id_q}' ORDER BY EVENT_TS DESC",
        missing_objects,
    )

    detail = detail_df.iloc[0].to_dict() if not detail_df.empty else None
    synopsis = defendant_df.iloc[0].to_dict() if not defendant_df.empty else {}
    confidence_summary = get_claim_confidence_summary(
        session=session,
        claim_id=claim_id,
        claim_detail=detail,
        synopsis=synopsis,
        sections_df=sections_df,
        missing_objects=missing_objects,
    )
    section_confidence = get_claim_section_confidence(sections_df)

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

    used_objects = {
        DETAIL_VIEW,
        FORM_VIEW,
        "MFQ_CLAIM_DEFENDANTS",
        "MFQ_RECORD_SUMMARY",
        "MFQ_MEDCRON_SUMMARY",
        "MFQ_LEGAL_MEMO",
        "MFQ_DOCUMENTS",
        "MFQ_ASSIGNMENT_QUEUE_VW",
        "MFQ_STATUS_HISTORY",
        LLM_EVAL_TABLE,
    }

    return {
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


def get_claim_section_confidence(sections_df: pd.DataFrame) -> pd.DataFrame:
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
        defendant_id_q = quote_sql(str(defendant_id))
        llm_eval_df = safe_collect_df(
            session,
            f"""
            SELECT NEEDS_HUMAN_REVIEW, FAITHFULNESS_SCORE
            FROM {LLM_EVAL_TABLE}
            WHERE ENTITY_ID = '{defendant_id_q}'
            ORDER BY CREATED_AT DESC
            LIMIT 1
            """,
        )
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
    claim_id_q = quote_sql(claim_id)
    status_q = quote_sql(new_status)
    session.sql(
        f"UPDATE MFQ_CLAIMS SET STATUS = '{status_q}', LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE CLAIM_ID = '{claim_id_q}'"
    ).collect()
    if assigned_to:
        assigned_q = quote_sql(assigned_to)
        session.sql(
            f"""
            UPDATE MFQ_ASSIGNMENTS ca
               SET LAST_UPDATED_TS = CURRENT_TIMESTAMP()
             WHERE CLAIM_ID = '{claim_id_q}'
               AND ASSIGNED_TO_USER_ID IN (SELECT USER_ID FROM MFQ_USERS WHERE USERNAME = '{assigned_q}')
            """
        ).collect()


def save_section_answer(session, answer_id: str, answer_text: str) -> None:
    answer_q = quote_sql(answer_text)
    answer_id_q = quote_sql(answer_id)
    if not answer_id_q:
        return
    session.sql(
        f"UPDATE MFQ_ANSWERS SET ANSWER_TEXT = '{answer_q}', LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE ANSWER_ID = '{answer_id_q}'"
    ).collect()
