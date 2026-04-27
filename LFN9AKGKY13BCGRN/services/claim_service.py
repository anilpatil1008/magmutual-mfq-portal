from __future__ import annotations

import json
from typing import Any

import pandas as pd

from services.snowflake_service import quote_sql, safe_collect_df


CLAIMS_VIEW = "MFQ_RECENT_CLAIMS_VW"
DETAIL_VIEW = "MFQ_CLAIM_DETAIL_VW"
FORM_VIEW = "MFQ_FORM_WORKSPACE_VW"


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
        "CLAIM_DEFENDANT",
        f"SELECT * FROM CLAIM_DEFENDANT WHERE CLAIM_ID = '{claim_id_q}'",
        missing_objects,
    )
    summary_df = _safe_read(
        session,
        "CLAIM_SUMMARY",
        f"SELECT SUMMARY_TYPE, SUMMARY_TEXT, GENERATED_TS FROM CLAIM_SUMMARY WHERE CLAIM_ID = '{claim_id_q}' ORDER BY GENERATED_TS DESC",
        missing_objects,
    )
    docs_df = _safe_read(
        session,
        "CLAIM_DOCUMENT",
        f"SELECT * FROM CLAIM_DOCUMENT WHERE CLAIM_ID = '{claim_id_q}' ORDER BY CREATED_TS DESC",
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
        "CLAIM_ENQUIRY",
        f"SELECT * FROM CLAIM_ENQUIRY WHERE CLAIM_ID = '{claim_id_q}' ORDER BY CREATED_TS DESC",
        missing_objects,
    )

    detail = detail_df.iloc[0].to_dict() if not detail_df.empty else None
    synopsis = defendant_df.iloc[0].to_dict() if not defendant_df.empty else {}

    section_confidence = pd.DataFrame()
    if not sections_df.empty:
        section_confidence = (
            sections_df.groupby(["SECTION_NAME", "SECTION_ORDER"], dropna=False)["CONFIDENCE_SCORE"]
            .mean()
            .reset_index()
            .sort_values(["SECTION_ORDER", "SECTION_NAME"])
        )

    overall_conf = None
    if detail and detail.get("AI_CONFIDENCE") is not None:
        overall_conf = float(detail["AI_CONFIDENCE"]) * 100 if float(detail["AI_CONFIDENCE"]) <= 1 else float(detail["AI_CONFIDENCE"])
    elif not sections_df.empty and sections_df["CONFIDENCE_SCORE"].notna().any():
        raw_mean = sections_df["CONFIDENCE_SCORE"].dropna().mean()
        overall_conf = float(raw_mean) * 100 if raw_mean <= 1 else float(raw_mean)

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
        "CLAIM_DEFENDANT",
        "CLAIM_SUMMARY",
        "CLAIM_DOCUMENT",
        "MFQ_ASSIGNMENT_QUEUE_VW",
        "CLAIM_ENQUIRY",
    }

    return {
        "claim": detail,
        "sections": sections_df,
        "synopsis": synopsis,
        "section_confidence": section_confidence,
        "overall_confidence": overall_conf,
        "summaries": summary_map,
        "documents": docs_df,
        "assignment": assignment_df,
        "enquiries": enquiries_df,
        "missing_objects": sorted(set(missing_objects)),
        "used_objects": sorted(used_objects),
    }


def update_claim_status(session, claim_id: str, new_status: str, assigned_to: str | None = None) -> None:
    claim_id_q = quote_sql(claim_id)
    status_q = quote_sql(new_status)
    session.sql(
        f"UPDATE CLAIM SET CLAIM_STATUS = '{status_q}', LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE CLAIM_ID = '{claim_id_q}'"
    ).collect()
    if assigned_to:
        assigned_q = quote_sql(assigned_to)
        session.sql(
            f"""
            UPDATE CLAIM_ASSIGNMENT ca
               SET LAST_UPDATED_TS = CURRENT_TIMESTAMP()
             WHERE CLAIM_ID = '{claim_id_q}'
               AND ASSIGNED_TO_USER_ID IN (SELECT USER_ID FROM APP_USER WHERE USERNAME = '{assigned_q}')
            """
        ).collect()


def save_section_answer(session, answer_id: str, answer_text: str) -> None:
    answer_q = quote_sql(answer_text)
    answer_id_q = quote_sql(answer_id)
    if not answer_id_q:
        return
    session.sql(
        f"UPDATE MFQ_ANSWER SET ANSWER_TEXT = '{answer_q}', LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE ANSWER_ID = '{answer_id_q}'"
    ).collect()
