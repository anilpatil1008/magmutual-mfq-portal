from __future__ import annotations

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
