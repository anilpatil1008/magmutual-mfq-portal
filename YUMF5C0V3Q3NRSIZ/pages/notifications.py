from __future__ import annotations

import pandas as pd
import streamlit as st


def render_notification_center(df: pd.DataFrame) -> None:
    if df.empty:
        st.caption("No notifications.")
        return

    for _, row in df.iterrows():
        severity = str(row.get("SEVERITY", "info")).lower()
        title = row.get("TITLE", "Notification")
        message = row.get("MESSAGE", "")
        created = row.get("CREATED_TS", "")
        st.markdown(
            f"<div class='mm-notif mm-notif-{severity}'><strong>{title}</strong><br>{message}<br><small>{created}</small></div>",
            unsafe_allow_html=True,
        )
