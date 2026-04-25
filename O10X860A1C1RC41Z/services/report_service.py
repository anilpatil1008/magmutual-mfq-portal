from __future__ import annotations

from services.claim_service import get_claims_queue


def get_report_frame(session, app_role: str, username: str):
    return get_claims_queue(session, app_role=app_role, username=username)
