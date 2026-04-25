from __future__ import annotations

import pandas as pd

from services.claim_service import get_claims_queue


def get_dashboard_metrics(session, app_role: str, username: str) -> dict[str, int]:
    claims = get_claims_queue(session, app_role=app_role, username=username)
    if claims.empty:
        return {
            "Total Active Claims": 0,
            "MFQ Generated": 0,
            "Assigned": 0,
            "Approved": 0,
            "Rejected": 0,
        }

    status = claims["STATUS"].fillna("")
    return {
        "Total Active Claims": int(len(claims)),
        "MFQ Generated": int((status == "MFQ Generated").sum()),
        "Assigned": int((status == "Assigned").sum()),
        "Approved": int((status == "Approved").sum()),
        "Rejected": int((status == "Rejected").sum()),
    }


def get_dashboard_charts(session, app_role: str, username: str) -> dict[str, pd.DataFrame]:
    claims = get_claims_queue(session, app_role=app_role, username=username)
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
