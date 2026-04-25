from __future__ import annotations

from typing import Any

import pandas as pd

from services.snowflake_service import quote_sql, safe_collect_df


CLAIMS_VIEW = "MFQ_CLAIMS_VW"


def _apply_rbac(df: pd.DataFrame, app_role: str, username: str) -> pd.DataFrame:
    if df.empty or app_role in {"Admin", "Executive"}:
        return df

    if app_role in {"Claims Analyst", "Advice Team"}:
        return df[df["STATUS"].isin(["MFQ Generated", "Assigned", "Approved", "Rejected"])].copy()

    if app_role == "Medical Faculty":
        return df[(df["ASSIGNED_TO"].fillna("").str.upper() == username.upper())].copy()

    return df.head(0)


def get_claims_queue(
    session,
    app_role: str,
    username: str,
    search_text: str = "",
    status_filter: str = "All",
) -> pd.DataFrame:
    df = safe_collect_df(session, f"SELECT * FROM {CLAIMS_VIEW}")
    if df.empty:
        return df

    scoped = _apply_rbac(df, app_role, username)

    if search_text.strip():
        needle = search_text.strip().lower()
        mask = (
            scoped["CLAIM_ID"].astype(str).str.lower().str.contains(needle)
            | scoped["PATIENT_NAME"].astype(str).str.lower().str.contains(needle)
            | scoped["DEFENDANT_NAME"].astype(str).str.lower().str.contains(needle)
            | scoped["FILE_NUMBER"].astype(str).str.lower().str.contains(needle)
        )
        scoped = scoped[mask]

    if status_filter != "All":
        scoped = scoped[scoped["STATUS"] == status_filter]

    if "DATE_REQUESTED" in scoped.columns:
        scoped = scoped.sort_values("DATE_REQUESTED", ascending=False)

    return scoped


def get_claim_details(session, claim_id: str) -> dict[str, Any] | None:
    claim_id_q = quote_sql(claim_id)
    df = safe_collect_df(session, f"SELECT * FROM {CLAIMS_VIEW} WHERE CLAIM_ID = '{claim_id_q}'")
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def get_claim_sections(session, claim_id: str) -> pd.DataFrame:
    claim_id_q = quote_sql(claim_id)
    sql = f"""
    WITH claim_defendant AS (
      SELECT DEFENDANT_ID
      FROM CLAIM_DEFENDANT
      WHERE CLAIM_ID = '{claim_id_q}'
      QUALIFY ROW_NUMBER() OVER (ORDER BY UPDATED_AT DESC, CREATED_AT DESC, DEFENDANT_ID) = 1
    ),
    latest_answers AS (
      SELECT
        a.ANSWER_ID,
        a.QUESTION_ID,
        a.ANSWER_TEXT,
        a.CONFIDENCE_SCORE
      FROM MFQ_ANSWER a
      INNER JOIN claim_defendant cd
        ON cd.DEFENDANT_ID = a.DEFENDANT_ID
      QUALIFY ROW_NUMBER() OVER (
        PARTITION BY a.QUESTION_ID
        ORDER BY IFF(a.IS_CURRENT, 1, 0) DESC, a.ANSWER_VERSION DESC, a.CREATED_AT DESC
      ) = 1
    )
    SELECT
      s.SECTION_NAME,
      s.DISPLAY_ORDER AS SECTION_ORDER,
      q.QUESTION_TEXT,
      q.DISPLAY_ORDER AS QUESTION_ORDER,
      COALESCE(la.ANSWER_TEXT, '') AS ANSWER_TEXT,
      la.CONFIDENCE_SCORE,
      la.ANSWER_ID
    FROM QST_SECTION s
    INNER JOIN QST_QUESTION q
      ON q.SECTION_ID = s.SECTION_ID
    LEFT JOIN latest_answers la
      ON la.QUESTION_ID = q.QUESTION_ID
    WHERE q.IS_CURRENT = TRUE
      AND q.IS_ACTIVE = TRUE
      AND s.IS_ACTIVE = TRUE
    ORDER BY s.DISPLAY_ORDER, q.DISPLAY_ORDER
    """
    return safe_collect_df(session, sql)


def get_status_values(session) -> list[str]:
    df = safe_collect_df(session, f"SELECT DISTINCT STATUS FROM {CLAIMS_VIEW} ORDER BY STATUS")
    statuses = [str(v) for v in df["STATUS"].dropna().tolist()] if not df.empty else []
    return ["All", *statuses]


def update_claim_status(session, claim_id: str, new_status: str, assigned_to: str | None = None) -> None:
    claim_id_q = quote_sql(claim_id)
    status_q = quote_sql(new_status)
    assigned_sql = (
        f", ASSIGNED_TO = '{quote_sql(assigned_to)}'" if assigned_to else ""
    )
    sql = f"""
    UPDATE MFQ_CLAIMS
    SET STATUS = '{status_q}', LAST_UPDATED_TS = CURRENT_TIMESTAMP() {assigned_sql}
    WHERE CLAIM_ID = '{claim_id_q}'
    """
    session.sql(sql).collect()


def save_section_answer(session, answer_id: str, answer_text: str) -> None:
    answer_q = quote_sql(answer_text)
    answer_id_q = quote_sql(answer_id)
    sql = f"""
    UPDATE MFQ_ANSWERS
    SET ANSWER_TEXT = '{answer_q}', LAST_UPDATED_TS = CURRENT_TIMESTAMP()
    WHERE ANSWER_ID = '{answer_id_q}'
    """
    session.sql(sql).collect()
