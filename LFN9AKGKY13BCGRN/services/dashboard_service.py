from __future__ import annotations

import pandas as pd

from repositories import dashboard_repository
from services.claim_service import get_claims_queue


def get_dashboard_metrics(session, username: str) -> dict[str, int]:
    metrics = {
        "Total Active Claims": 0,
        "MFQ Generated": 0,
        "Assigned": 0,
        "On Hold": 0,
        "Approved": 0,
        "Rejected": 0,
    }
    df = dashboard_repository.get_dashboard_kpis(session)
    if df.empty:
        return metrics

    row = df.iloc[0]
    return {
        "Total Active Claims": int(row.get("TOTAL_ACTIVE_CLAIMS") or 0),
        "MFQ Generated": int(row.get("MFQ_GENERATED") or 0),
        "Assigned": int(row.get("ASSIGNED") or 0),
        "On Hold": int(row.get("ON_HOLD") or 0),
        "Approved": int(row.get("APPROVED") or 0),
        "Rejected": int(row.get("REJECTED") or 0),
    }


def get_dashboard_charts(session, username: str) -> dict[str, pd.DataFrame]:
    claims = get_claims_queue(session, username=username)
    if claims.empty:
        return {
            "status": pd.DataFrame(columns=["STATUS", "COUNT"]),
            "specialty": pd.DataFrame(columns=["SPECIALTY", "COUNT"]),
            "priority": pd.DataFrame(columns=["PRIORITY", "COUNT"]),
        }

    return {
        "status": claims.groupby("STATUS").size().reset_index(name="COUNT"),
        "specialty": claims.groupby("SPECIALTY").size().reset_index(name="COUNT"),
        "priority": claims.groupby("PRIORITY").size().reset_index(name="COUNT"),
    }
