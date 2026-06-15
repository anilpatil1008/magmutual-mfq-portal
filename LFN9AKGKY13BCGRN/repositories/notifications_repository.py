from __future__ import annotations

import logging

import pandas as pd

from config import snowflake_objects as obj
from core.query_executor import app_debug_enabled, execute_query_df
from repositories.claims_repository import object_exists
from services.snowflake_service import quote_sql

logger = logging.getLogger(__name__)
_MISSING_NOTIFICATIONS_VIEW_LOGGED = False


def _empty_notifications_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["NOTIFICATION_ID", "TITLE", "MESSAGE", "SEVERITY", "CREATED_TS", "IS_READ"]
    )


def _notifications_view_available(session) -> bool:
    global _MISSING_NOTIFICATIONS_VIEW_LOGGED
    exists = object_exists(session, obj.MFQ_NOTIFICATIONS_VIEW)
    if not exists and app_debug_enabled() and not _MISSING_NOTIFICATIONS_VIEW_LOGGED:
        logger.debug(
            "notifications view unavailable; header will render with empty notifications view=%s",
            obj.MFQ_NOTIFICATIONS_VIEW,
        )
        _MISSING_NOTIFICATIONS_VIEW_LOGGED = True
    return exists


def get_notifications_for_user(session, username: str, limit: int = 10) -> pd.DataFrame:
    if not _notifications_view_available(session):
        return _empty_notifications_df()

    username_q = quote_sql(username)
    sql = f"""
    SELECT
        NOTIFICATION_ID,
        COALESCE(EVENT_TITLE, 'Notification') AS TITLE,
        COALESCE(EVENT_MESSAGE, '') AS MESSAGE,
        LOWER(COALESCE(EVENT_PRIORITY, 'info')) AS SEVERITY,
        EVENT_TS AS CREATED_TS,
        IS_READ
    FROM {obj.MFQ_NOTIFICATIONS_VIEW}
    WHERE UPPER(COALESCE(USERNAME, '')) = UPPER('{username_q}')
       OR UPPER(COALESCE(USERNAME, '')) = 'ALL'
    ORDER BY EVENT_TS DESC
    LIMIT {int(limit)}
    """
    return execute_query_df(
        session,
        sql,
        fallback=_empty_notifications_df(),
        query_name="notifications.get_notifications_for_user",
    )


def mark_notification_read_by_id(session, notification_id: str) -> None:
    if not object_exists(session, obj.MFQ_NOTIFICATIONS_TABLE):
        return
    notification_id_q = quote_sql(notification_id)
    execute_query_df(
        session,
        f"UPDATE {obj.MFQ_NOTIFICATIONS_TABLE} SET IS_READ = TRUE WHERE NOTIFICATION_ID = '{notification_id_q}'",
        query_name="notifications.mark_notification_read",
    )
