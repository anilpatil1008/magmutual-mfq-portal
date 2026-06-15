from __future__ import annotations

import pandas as pd
import streamlit as st

from repositories.notifications_repository import get_notifications_for_user, mark_notification_read_by_id


@st.cache_data(ttl=60, show_spinner=False)
def _cached_notifications(username: str, limit: int) -> pd.DataFrame:
    from services.snowflake_service import get_session

    session = get_session()
    return get_notifications_for_user(session, username, limit)


def get_user_notifications(session, username: str, limit: int = 10) -> pd.DataFrame:
    del session
    return _cached_notifications(username, int(limit))


def mark_notification_read(session, notification_id: str) -> None:
    mark_notification_read_by_id(session, notification_id)
    _cached_notifications.clear()
