from __future__ import annotations

import html
from typing import Any, Iterable, Mapping

import streamlit as st


ICON_CLASS_MAP = {
    "📄": "icon-doc",
    "!": "icon-info",
    "🕒": "icon-clock",
    "✓": "icon-success",
    "✕": "icon-danger",
}


MetricItem = Mapping[str, Any]


def _metric_card_html(title: str, value: Any, subtitle: str = "", icon: str = "") -> str:
    icon_html = ""
    if icon:
        icon_class = ICON_CLASS_MAP.get(icon, "")
        icon_html = f"<div class='metric-icon {icon_class}'>{html.escape(icon)}</div>"

    subtitle_html = (
        f"<div class='metric-subtitle'>{html.escape(subtitle)}</div>"
        if subtitle
        else "<div class='metric-subtitle metric-subtitle-empty'>&nbsp;</div>"
    )

    return f"""
    <div class="metric-card">
        <div class="metric-card-top">
            <div class="metric-label">{html.escape(str(title))}</div>
            {icon_html}
        </div>
        <div class="metric-value">{html.escape(str(value))}</div>
        {subtitle_html}
    </div>
    """


def render_metric_card(title: str, value: Any, subtitle: str = "", icon: str = "") -> None:
    st.markdown(_metric_card_html(title, value, subtitle, icon), unsafe_allow_html=True)


def render_metric_grid(metrics: Iterable[MetricItem]) -> None:
    """Render metric cards with Streamlit columns instead of one large HTML grid.

    Streamlit can display raw HTML text when large nested HTML blocks are injected as a
    single markdown payload in some environments. Rendering each card in its own column
    keeps the layout stable and enterprise-friendly.
    """
    metric_list = list(metrics)
    if not metric_list:
        return

    st.markdown('<div class="metrics-row-shell"></div>', unsafe_allow_html=True)
    columns = st.columns(len(metric_list), gap="medium")

    for column, item in zip(columns, metric_list):
        with column:
            render_metric_card(
                str(item.get("title", "")),
                item.get("value", ""),
                str(item.get("subtitle", "")),
                str(item.get("icon", "")),
            )

    st.markdown('<div class="metrics-row-bottom-space"></div>', unsafe_allow_html=True)
