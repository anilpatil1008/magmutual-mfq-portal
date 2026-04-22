from __future__ import annotations

import html
from typing import Any

import streamlit as st


def render_metric_card(title: str, value: Any, subtitle: str = "", icon: str = "") -> None:
    icon_html = (
        f"<div class='metric-icon'>{html.escape(icon)}</div>"
        if icon else ""
    )

    subtitle_html = (
        f"<div class='metric-subtitle'>{html.escape(subtitle)}</div>"
        if subtitle else "<div style='height:22px;'></div>"
    )

    st.markdown(
        f"""
        <div class="metric-card">
            {icon_html}
            <div class="metric-label">{html.escape(str(title))}</div>
            <div class="metric-value">{html.escape(str(value))}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )