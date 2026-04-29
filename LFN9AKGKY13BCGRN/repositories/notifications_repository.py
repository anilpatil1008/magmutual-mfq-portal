from __future__ import annotations

import pandas as pd

from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql


def get_notifications_for_user(session, username: str, limit: int = 10) -> pd.DataFrame:
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
    return execute_query_df(session, sql, query_name="notifications.get_notifications_for_user")


def mark_notification_read_by_id(session, notification_id: str) -> None:
    notification_id_q = quote_sql(notification_id)
    execute_query_df(
        session,
        f"UPDATE {obj.MFQ_NOTIFICATIONS_TABLE} SET IS_READ = TRUE WHERE NOTIFICATION_ID = '{notification_id_q}'",
        query_name="notifications.mark_notification_read",
    )
