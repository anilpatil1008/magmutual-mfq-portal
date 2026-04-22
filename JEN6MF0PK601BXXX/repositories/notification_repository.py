from __future__ import annotations

from config.settings import CONFIG
from repositories.base_repository import run_query, esc


def get_notifications(user_id: str):
    return run_query(f"""
        SELECT NOTIFICATION_ID, CLAIM_ID, EVENT_TYPE, MESSAGE, IS_READ, CREATED_AT
        FROM {CONFIG.database}.{CONFIG.schema}.APP_NOTIFICATION
        WHERE USER_ID = '{esc(user_id)}'
        ORDER BY CREATED_AT DESC
    """)
