from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from components.badges import render_legend
from components.cards import render_kpi_cards
from components.tables import render_recent_claims_table
from services.claim_service import get_claims_queue
from services.dashboard_service import get_dashboard_metrics


def _safe_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series([], dtype="object")
    return df[column]


def _build_focus_items(queue: pd.DataFrame) -> list[dict[str, Any]]:
    if queue.empty:
        return [
            {"label": "High Priority", "value": 0, "tone": "warning"},
            {"label": "Unassigned", "value": 0, "tone": "neutral"},
            {"label": "Pending Review", "value": 0, "tone": "info"},
        ]

    priority = _safe_series(queue, "PRIORITY").astype(str).str.strip().str.lower()
    status = _safe_series(queue, "STATUS").astype(str).str.strip().str.lower()
    assigned = _safe_series(queue, "ASSIGNED_TO").astype(str).str.strip().str.lower()

    high_priority = int(priority.isin(["critical", "high"]).sum())
    unassigned = int(assigned.isin(["", "none", "nan", "unassigned", "tbd"]).sum())
    pending_review = int(status.isin(["assigned", "mfq generated", "pending"]).sum())

    return [
        {"label": "High Priority", "value": high_priority, "tone": "warning"},
        {"label": "Unassigned", "value": unassigned, "tone": "neutral"},
        {"label": "Pending Review", "value": pending_review, "tone": "info"},
    ]


def _render_focus_strip(items: list[dict[str, Any]]) -> None:
    cards = []
    for item in items:
        label = escape(str(item.get("label", "Metric")))
        value = escape(str(item.get("value", 0)))
        tone = escape(str(item.get("tone", "neutral")))
        cards.append(
            "".join(
                [
                    f"<article class='mm-focus-item tone-{tone}'>",
                    f"<div class='mm-focus-value'>{value}</div>",
                    f"<div class='mm-focus-label'>{label}</div>",
                    "</article>",
                ]
            )
        )

    st.markdown(
        f"<section class='mm-focus-strip'>{''.join(cards)}</section>",
        unsafe_allow_html=True,
    )


def _status_filter_options(queue: pd.DataFrame) -> list[str]:
    statuses = sorted({str(value).strip() for value in _safe_series(queue, "STATUS") if str(value).strip()})
    return ["All Statuses", *statuses]


def _resolve_user_display_name(ctx) -> str:
    candidate_values = [
        getattr(ctx, "full_name", None),
        getattr(ctx, "name", None),
        st.session_state.get("full_name"),
        st.session_state.get("user_full_name"),
        st.session_state.get("username"),
        st.session_state.get("user_email"),
    ]

    user_profile = st.session_state.get("user_profile")
    if isinstance(user_profile, dict):
        candidate_values.extend(
            [
                user_profile.get("full_name"),
                user_profile.get("name"),
                user_profile.get("username"),
                user_profile.get("email"),
            ]
        )

    for candidate in candidate_values:
        value = str(candidate or "").strip()
        if value:
            return value

    return str(getattr(ctx, "username", "") or "").strip()


def render(session, ctx) -> None:
    st.title("Dashboard")
    display_name = _resolve_user_display_name(ctx)
    if display_name:
        st.markdown(
            (
                f"<p class='mm-dashboard-welcome'>Welcome back, {escape(display_name)}. "
                "Here's what's happening today.</p>"
            ),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<p class='mm-dashboard-welcome'>Welcome back. Here's what's happening today.</p>",
            unsafe_allow_html=True,
        )

    metrics = get_dashboard_metrics(session, app_role=ctx.app_role, username=ctx.username)
    render_kpi_cards(metrics)
    render_legend()

    card_key = "dash_recent_claims"
    search = st.session_state.get(f"{card_key}_search", "")

    base_queue = get_claims_queue(session, ctx.app_role, ctx.username, search_text=search)
    _render_focus_strip(_build_focus_items(base_queue))

    filter_options = _status_filter_options(base_queue)
    current_filter = st.session_state.get(f"{card_key}_status_filter", "All Statuses")
    if current_filter not in filter_options:
        current_filter = "All Statuses"

    with st.container(key="recent_claims_card"):
        header_left, header_right = st.columns([4, 3], vertical_alignment="top")
        with header_left:
            st.markdown(
                (
                    "<div class='recent-claims-heading'>"
                    "<h3 class='recent-claims-title'>Recent Claims</h3>"
                    "<p class='recent-claims-subtitle'>Latest claims submitted for assessment.</p>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
        with header_right:
            st.markdown("<div class='recent-claims-toolbar'>", unsafe_allow_html=True)
            search_col, filter_col, report_col = st.columns([3.2, 1.25, 1.8], gap="small")
            with search_col:
                with st.container(key="recent_claims_search"):
                    search = st.text_input(
                        "Search",
                        value=search,
                        placeholder="Search by patient, file #...",
                        label_visibility="collapsed",
                        key=f"{card_key}_search",
                    )
            with filter_col:
                st.button(
                    "Filters",
                    key="dash_claim_filters",
                    type="secondary",
                    use_container_width=True,
                )
            with report_col:
                if st.button(
                    "Generate Report",
                    key="dash_generate_report",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.active_page = "Reports"
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        render_recent_claims_table(filtered_queue.head(20), key_prefix="dash")
