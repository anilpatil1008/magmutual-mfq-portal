from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st


def render_notification_center(df: pd.DataFrame) -> None:
    total = int(len(df.index))
    unread = int((~df["IS_READ"]).sum()) if "IS_READ" in df.columns else total

    st.markdown("<div class='mm-notif-panel'>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="mm-notif-panel-header">
            <div class="mm-notif-panel-title-wrap">
                <span class="mm-notif-panel-title">Notifications</span>
                <span class="mm-notif-panel-count">{unread}</span>
            </div>
            <span class="mm-notif-mark-read">Mark all read</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.markdown("<div class='mm-notif-empty'>No notifications.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    notif_html = ["<div class='mm-notif-scroll'>"]
    for _, row in df.iterrows():
        severity = escape(str(row.get("SEVERITY", "info")).lower())
        claim_id = escape(str(row.get("CLAIM_ID", "N/A")))
        title = escape(str(row.get("TITLE", "Notification")))
        message = escape(str(row.get("MESSAGE", "")))
        created = escape(str(row.get("CREATED_TS", "")))
        is_read = bool(row.get("IS_READ", False))
        unread_class = " mm-notif-item-unread" if not is_read else ""

        notif_html.append(
            f"""
            <article class="mm-notif-item mm-notif-{severity}{unread_class}">
                <div class="mm-notif-item-icon" aria-hidden="true">{_icon_for_severity(severity)}</div>
                <div class="mm-notif-item-body">
                    <div class="mm-notif-item-top">
                        <span class="mm-notif-claim">Claim #{claim_id}</span>
                        <span class="mm-notif-time">{created}</span>
                    </div>
                    <div class="mm-notif-title">{title}</div>
                    <div class="mm-notif-message">{message}</div>
                </div>
            </article>
            """
        )

    notif_html.append("</div>")
    st.markdown("".join(notif_html), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _icon_for_severity(severity: str) -> str:
    icons = {
        "warning": "⚠️",
        "danger": "⛔",
        "error": "⛔",
        "success": "✅",
        "info": "ℹ️",
    }
    return icons.get(severity, "ℹ️")
