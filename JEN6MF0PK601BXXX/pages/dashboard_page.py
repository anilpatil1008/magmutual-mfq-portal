from __future__ import annotations

import streamlit as st

from components.cards import render_metric_card
from components.layout import render_page_title
from components.tables import render_claims_table
from core.constants import CLAIM_PRIORITIES, CLAIM_STATUSES
from repositories.claim_repository import get_claim_queue, get_dashboard_metrics
from services.claim_service import request_regeneration


def render_dashboard(display_name: str, user_id: str) -> None:
    top_left, top_right = st.columns([5, 1.2])

    with top_left:
        render_page_title(
            "Dashboard",
            f"Welcome back, {display_name}. Here's what's happening today.",
        )

    with top_right:
        st.button("Generate Report", use_container_width=True, key="dashboard_generate_report_btn")

    metrics_df = get_dashboard_metrics()
    if not metrics_df.empty:
        m = metrics_df.iloc[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            render_metric_card("Total Active\nClaims", int(m["TOTAL_ACTIVE_CLAIMS"]), "+12%  vs last month", "📄")
        with c2:
            render_metric_card("MFQ Generated", int(m["MFQ_GENERATED"]), "", "!")
        with c3:
            render_metric_card("Assigned", int(m["ASSIGNED"]), "", "🕒")
        with c4:
            render_metric_card("Approved", int(m["APPROVED"]), "", "✓")
        with c5:
            render_metric_card("Rejected", int(m["REJECTED"]), "", "✕")

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    status_col, priority_col = st.columns([2, 2])

    selected_status = status_col.multiselect(
        "Status",
        CLAIM_STATUSES,
        key="dashboard_status_filter",
    )

    selected_priority = priority_col.multiselect(
        "Priority",
        CLAIM_PRIORITIES,
        key="dashboard_priority_filter",
    )

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
        st.success("Regeneration requested")
        st.rerun()

    render_claims_table(
        queue_df=queue_df,
        on_review=_review,
        on_regenerate=_regen,
    )