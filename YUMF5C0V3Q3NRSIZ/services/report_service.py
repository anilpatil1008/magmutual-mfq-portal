from __future__ import annotations

import pandas as pd

from services.claim_service import get_claims_queue


def get_report_frames(session, app_role: str, username: str) -> dict[str, pd.DataFrame]:
    """Return report-ready grouped dataframes scoped by app RBAC."""
    df = get_claims_queue(session, app_role=app_role, username=username)
    if df.empty:
        return {
            "status": pd.DataFrame(columns=["STATUS", "COUNT"]),
            "priority": pd.DataFrame(columns=["PRIORITY", "COUNT"]),
            "specialty": pd.DataFrame(columns=["SPECIALTY", "COUNT"]),
            "faculty": pd.DataFrame(columns=["ASSIGNED_TO", "TOTAL"]),
        }

    faculty = (
        df.groupby("ASSIGNED_TO", dropna=False)
        .agg(TOTAL=("CLAIM_ID", "count"))
        .reset_index()
        .sort_values("TOTAL", ascending=False)
    )

    return {
        "status": df.groupby("STATUS").size().reset_index(name="COUNT"),
        "priority": df.groupby("PRIORITY").size().reset_index(name="COUNT"),
        "specialty": df.groupby("SPECIALTY").size().reset_index(name="COUNT"),
        "faculty": faculty,
    }
