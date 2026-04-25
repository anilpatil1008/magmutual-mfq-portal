from __future__ import annotations

import pandas as pd

from services.snowflake_service import quote_sql, safe_collect_df


def get_user_notifications(session, username: str, limit: int = 10) -> pd.DataFrame:
    username_q = quote_sql(username)
    sql = f"""
    SELECT NOTIFICATION_ID, TITLE, MESSAGE, SEVERITY, CREATED_TS, IS_READ
    FROM MFQ_NOTIFICATIONS_VW
    WHERE TARGET_USER = '{username_q}' OR TARGET_USER = 'ALL'
    ORDER BY CREATED_TS DESC
    LIMIT {int(limit)}
    """
    fallback = pd.DataFrame(
        [
            {
                "NOTIFICATION_ID": "local-1",
                "TITLE": "Welcome",
                "MESSAGE": "Portal initialized with demo fallback notifications.",
                "SEVERITY": "info",
                "CREATED_TS": None,
                "IS_READ": False,
            }
        ]
    )
    return safe_collect_df(session, sql, fallback=fallback)


def mark_notification_read(session, notification_id: str) -> None:
    notification_id_q = quote_sql(notification_id)
    session.sql(
        f"UPDATE MFQ_NOTIFICATIONS SET IS_READ = TRUE, READ_TS = CURRENT_TIMESTAMP() WHERE NOTIFICATION_ID = '{notification_id_q}'"
    ).collect()
