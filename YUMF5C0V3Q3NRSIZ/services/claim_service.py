from __future__ import annotations

from typing import Any

import pandas as pd

from services.snowflake_service import quote_sql, safe_collect_df


CLAIMS_VIEW = "MFQ_CLAIMS_VW"
SECTIONS_VIEW = "MFQ_SECTIONS_VW"


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
    # Some environments expose MFQ_SECTIONS_VW with a different claim identifier
    # column shape than CLAIM_ID (for example CLAIM_NUMBER). To avoid runtime SQL
    # compilation failures on unknown identifiers, load then filter in-memory.
    df = safe_collect_df(session, f"SELECT * FROM {SECTIONS_VIEW}")
    if df.empty:
        return df

    claim_columns = ("CLAIM_ID", "CLAIM_NUMBER", "CLAIMNO", "CLAIM")
    scoped = df
    for column in claim_columns:
        if column in scoped.columns:
            scoped = scoped[scoped[column].astype(str) == str(claim_id)]
            break
    else:
        return df.head(0)

    order_cols = [c for c in ("SECTION_ORDER", "QUESTION_ORDER") if c in scoped.columns]
    if order_cols:
        scoped = scoped.sort_values(order_cols)

    return scoped


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
