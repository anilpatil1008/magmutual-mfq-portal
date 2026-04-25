from __future__ import annotations

from typing import Optional

import pandas as pd
from snowflake.snowpark.context import get_active_session


def get_session():
    return get_active_session()


def _apply_role_filter(df: pd.DataFrame, role: str, username: str) -> pd.DataFrame:
    if df.empty:
        return df
    if role in {"Admin", "Executive"}:
        return df
    if role in {"Claim Analyst", "Advice Team"}:
        return df[df["STATUS"].isin(["MFQ Generated", "Assigned", "Approved", "Rejected"])]
    if role == "Medical Faculty":
        return df[
            ((df["STATUS"] == "Assigned") & (df["ASSIGNED_TO"] == username))
            | ((df["STATUS"] == "Approved") & (df["APPROVED_BY"] == username))
        ]
    return df


def get_claims(session, role: str, username: str, search: str = "", status: Optional[str] = None) -> pd.DataFrame:
    df = session.table("MFQ_CLAIMS_VW").to_pandas()
    df = _apply_role_filter(df, role, username)
    if search:
        s = search.strip().lower()
        mask = (
            df["CLAIM_ID"].astype(str).str.lower().str.contains(s)
            | df["PATIENT_NAME"].astype(str).str.lower().str.contains(s)
            | df["DEFENDANT_NAME"].astype(str).str.lower().str.contains(s)
        )
        df = df[mask]
    if status and status != "All":
        df = df[df["STATUS"] == status]
    return df.sort_values("DATE_REQUESTED", ascending=False)


def get_claim_by_id(session, claim_id: str) -> pd.DataFrame:
    return session.table("MFQ_CLAIMS_VW").filter(f"CLAIM_ID = '{claim_id}'").to_pandas()


def get_mfq_sections(session, claim_id: str) -> pd.DataFrame:
    return (
        session.table("MFQ_SECTIONS")
        .filter(f"CLAIM_ID = '{claim_id}'")
        .sort("SECTION_ORDER", "QUESTION_ORDER")
        .to_pandas()
    )


def get_dashboard_metrics(session, role: str, username: str) -> dict:
    claims = _apply_role_filter(session.table("MFQ_CLAIMS_VW").to_pandas(), role, username)
    return {
        "Total Active Claims": int(len(claims)),
        "MFQ Generated": int((claims["STATUS"] == "MFQ Generated").sum()),
        "Assigned": int((claims["STATUS"] == "Assigned").sum()),
        "Approved": int((claims["STATUS"] == "Approved").sum()),
        "Rejected": int((claims["STATUS"] == "Rejected").sum()),
    }


def get_report_metrics(session, role: str, username: str) -> dict:
    claims = _apply_role_filter(session.table("MFQ_CLAIMS_VW").to_pandas(), role, username)
    return {
        "status": claims.groupby("STATUS").size().reset_index(name="COUNT"),
        "priority": claims.groupby("PRIORITY").size().reset_index(name="COUNT"),
        "specialty": claims.groupby("SPECIALTY").size().reset_index(name="COUNT"),
        "faculty": claims.groupby("ASSIGNED_TO").agg(
            TOTAL=("CLAIM_ID", "count"),
            APPROVED=("STATUS", lambda s: (s == "Approved").sum()),
        ).reset_index(),
    }


def update_claim_status(session, claim_id: str, new_status: str, assigned_to: Optional[str] = None) -> None:
    assignment_sql = f", ASSIGNED_TO = '{assigned_to}'" if assigned_to else ""
    session.sql(
        f"""
        UPDATE MFQ_CLAIMS
        SET STATUS = '{new_status}', LAST_UPDATED_TS = CURRENT_TIMESTAMP(){assignment_sql}
        WHERE CLAIM_ID = '{claim_id}'
        """
    ).collect()
