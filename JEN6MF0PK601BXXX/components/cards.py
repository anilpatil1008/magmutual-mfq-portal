from __future__ import annotations

import html
from typing import Any

import streamlit as st


ICON_CLASS_MAP = {
    "📄": "icon-doc",
    "!": "icon-info",
    "🕒": "icon-clock",
    "✓": "icon-success",
    "✕": "icon-danger",
}


def render_metric_card(title: str, value: Any, subtitle: str = "", icon: str = "") -> None:
    icon_html = ""
    if icon:
        icon_class = ICON_CLASS_MAP.get(icon, "")
        icon_html = (
            f"<div class='metric-icon {icon_class}'>{html.escape(icon)}</div>"
        )

    subtitle_html = (
        f"<div class='metric-subtitle'>{html.escape(subtitle)}</div>"
        if subtitle
        else "<div class='metric-subtitle metric-subtitle-empty'>&nbsp;</div>"
    )

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-card-top">
                <div class="metric-label">{html.escape(str(title))}</div>
                {icon_html}
            </div>
            <div class="metric-value">{html.escape(str(value))}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
