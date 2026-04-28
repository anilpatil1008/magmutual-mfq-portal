from __future__ import annotations

import json
from typing import Any

import pandas as pd

from services.snowflake_service import quote_sql, safe_collect_df


CLAIMS_VIEW = "MFQ_RECENT_CLAIMS_VW"
DETAIL_VIEW = "MFQ_CLAIM_DETAIL_VW"
FORM_VIEW = "MFQ_FORM_WORKSPACE_VW"
SECTIONS_TABLE = "MFQ_SECTIONS"
QUESTIONS_TABLE = "MFQ_QUESTIONS"
ANSWERS_TABLE = "MFQ_ANSWERS"
QUESTION_CONFIDENCE_TABLE = "MFQ_QUESTION_CONFIDENCE"
SECTION_CONFIDENCE_TABLE = "MFQ_SECTION_CONFIDENCE"
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


def get_mfq_form_workspace(session, claim_id: str, defendant_id: str | None = None) -> pd.DataFrame:
    claim_id_q = quote_sql(claim_id)
    answer_cols = _table_columns(session, ANSWERS_TABLE)
    question_conf_cols = _table_columns(session, QUESTION_CONFIDENCE_TABLE)

    answer_value_expr = "a.ANSWER_VALUE" if "ANSWER_VALUE" in answer_cols else "NULL"
    generated_answer_expr = "a.GENERATED_ANSWER" if "GENERATED_ANSWER" in answer_cols else "NULL"
    reviewed_answer_expr = "a.REVIEWED_ANSWER" if "REVIEWED_ANSWER" in answer_cols else "NULL"

    qc_level_expr = "qc.CONFIDENCE_LEVEL" if "CONFIDENCE_LEVEL" in question_conf_cols else "NULL"
    qc_reason_expr = "qc.CONFIDENCE_REASON" if "CONFIDENCE_REASON" in question_conf_cols else "NULL"

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
          ON a.QUESTION_ID = q.QUESTION_ID
         AND a.CLAIM_ID = '{claim_id_q}'
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
    defendant_df = _safe_read(
        session,
        "MFQ_CLAIM_DEFENDANTS",
        f"SELECT * FROM MFQ_CLAIM_DEFENDANTS WHERE CLAIM_ID = '{claim_id_q}'",
        missing_objects,
    )

    detail = detail_df.iloc[0].to_dict() if not detail_df.empty else None
    synopsis = defendant_df.iloc[0].to_dict() if not defendant_df.empty else {}
    defendant_id = synopsis.get("DEFENDANT_ID") or (detail.get("DEFENDANT_ID") if detail else None)

    sections_df = pd.DataFrame()
    form_objects = [SECTIONS_TABLE, QUESTIONS_TABLE, ANSWERS_TABLE, QUESTION_CONFIDENCE_TABLE]
    if all(_object_exists(session, obj) for obj in form_objects):
        sections_df = get_mfq_form_workspace(session, claim_id, defendant_id=str(defendant_id) if defendant_id else None)
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
    value = (
        row.get("REVIEWED_ANSWER")
        or row.get("ANSWER_VALUE")
        or row.get("ANSWER_TEXT")
        or extract_answer_json_value(row.get("ANSWER_JSON"))
        or row.get("GENERATED_ANSWER")
        or ""
    )
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
