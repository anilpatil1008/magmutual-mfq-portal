from __future__ import annotations

import streamlit as st

from components.cards import render_metric_card
from components.layout import render_page_title
from components.tables import render_claims_table
from core.constants import CLAIM_PRIORITIES, CLAIM_STATUSES
from repositories.claim_repository import get_claim_queue, get_dashboard_metrics
from services.claim_service import request_regeneration


METRIC_CONFIG = [
    ("Total Active\nClaims", "TOTAL_ACTIVE_CLAIMS", "+12% vs last month", "📄"),
    ("MFQ Generated", "MFQ_GENERATED", "", "!"),
    ("Assigned", "ASSIGNED", "", "🕒"),
    ("Approved", "APPROVED", "", "✓"),
    ("Rejected", "REJECTED", "", "✕"),
]


def render_dashboard(display_name: str, user_id: str) -> None:
    header_col, action_col = st.columns([5.5, 2.2], vertical_alignment="bottom")

    with header_col:
        render_page_title(
            "Dashboard",
            f"Welcome back, {display_name}. Here's what's happening today.",
        )

    with action_col:
        action_left, action_right = st.columns([1, 1.15], vertical_alignment="bottom")
        with action_left:
            with st.popover("Filters", use_container_width=True):
                st.markdown("### Filter claims")
                st.multiselect(
                    "Status",
                    CLAIM_STATUSES,
                    key="dashboard_status_filter",
                )
                st.multiselect(
                    "Priority",
                    CLAIM_PRIORITIES,
                    key="dashboard_priority_filter",
                )
        with action_right:
            st.button("Generate Report", use_container_width=True, key="dashboard_generate_report_btn", type="primary")

    metrics_df = get_dashboard_metrics()
    if not metrics_df.empty:
        metric_row = st.columns(5, gap="medium")
        values = metrics_df.iloc[0]
        for column, (label, field, subtitle, icon) in zip(metric_row, METRIC_CONFIG):
            with column:
                render_metric_card(label, int(values[field]), subtitle, icon)

    selected_status = st.session_state.get("dashboard_status_filter", [])
    selected_priority = st.session_state.get("dashboard_priority_filter", [])
    search_text = st.session_state.get("claims_table_inline_search", "")

    queue_df = get_claim_queue(
        search_text=search_text,
        status_filter=selected_status,
        priority_filter=selected_priority,
        confidence_band="All",
    )

    def _review(claim_id: str) -> None:
        st.session_state.selected_claim_id = claim_id
        st.session_state.page = "Claim Detail"
        st.rerun()

    def _regen(claim_id: str) -> None:
        request_regeneration(claim_id, user_id)
        st.toast("Regeneration requested")
        st.rerun()

    render_claims_table(
        queue_df=queue_df,
        on_review=_review,
        on_regenerate=_regen,
        show_regenerate=False,
        title="Recent Claims",
        subtitle="Latest claims submitted for assessment.",
        search_key="claims_table_inline_search",
    )
