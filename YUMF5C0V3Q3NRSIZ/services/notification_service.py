from __future__ import annotations

import pandas as pd

from services.snowflake_service import quote_sql, safe_collect_df


def get_user_notifications(session, username: str, limit: int = 10) -> pd.DataFrame:
    username_q = quote_sql(username)
    sql = f"""
    SELECT
        NOTIFICATION_ID,
        COALESCE(EVENT_TITLE, 'Notification') AS TITLE,
        COALESCE(EVENT_MESSAGE, '') AS MESSAGE,
        LOWER(COALESCE(EVENT_PRIORITY, 'info')) AS SEVERITY,
        EVENT_TS AS CREATED_TS,
        IS_READ
    FROM MFQ_NOTIFICATIONS_VW
    WHERE UPPER(COALESCE(USERNAME, '')) = UPPER('{username_q}')
       OR UPPER(COALESCE(USERNAME, '')) = 'ALL'
    ORDER BY EVENT_TS DESC
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
        f"""
        MERGE INTO NOTIFICATION_READ_STATUS rs
        USING (
            SELECT '{notification_id_q}' AS NOTIFICATION_ID, USER_ID
            FROM NOTIFICATION_EVENT
            WHERE NOTIFICATION_ID = '{notification_id_q}'
        ) src
        ON rs.NOTIFICATION_ID = src.NOTIFICATION_ID
         AND rs.USER_ID = src.USER_ID
        WHEN MATCHED THEN
          UPDATE SET READ_AT = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN
          INSERT (READ_STATUS_ID, NOTIFICATION_ID, USER_ID, READ_AT)
          VALUES (UUID_STRING(), src.NOTIFICATION_ID, src.USER_ID, CURRENT_TIMESTAMP())
        """
    ).collect()
