from __future__ import annotations

import streamlit as st

from components.badges import render_legend
from components.cards import render_kpi_cards
from components.tables import render_claims_table
from services.claim_service import get_claims_queue, get_status_values
from services.dashboard_service import get_dashboard_charts, get_dashboard_metrics


def render(session, ctx) -> None:
    st.markdown("<h1 class='mm-page-title'>Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='mm-page-subtitle'>Welcome back, {ctx.username.replace('_', ' ').title()}. Here's what's happening today.</div>",
        unsafe_allow_html=True,
    )

    head_left, head_right = st.columns([3.6, 1.4])
    with head_left:
        render_kpi_cards(get_dashboard_metrics(session, app_role=ctx.app_role, username=ctx.username))
    with head_right:
        st.markdown("<div class='mm-page-actions'>", unsafe_allow_html=True)
        st.button("Filter View", use_container_width=True, type="secondary", key="dash_filter")
        st.button("Generate Report", use_container_width=True, type="primary", key="dash_gen_report")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<section class='mm-panel'>", unsafe_allow_html=True)
    panel_head_left, panel_head_right = st.columns([2.6, 1.0])
    panel_head_left.markdown("### Recent Claims")
    panel_head_left.caption("Latest claims submitted for assessment.")

    search = panel_head_right.text_input("Search", placeholder="Search by patient, file #...", label_visibility="collapsed")

    f1, f2, f3 = st.columns([2.5, 1.6, 0.9])
    status = f2.selectbox("Status", get_status_values(session), index=0)
    if f3.button("Refresh", use_container_width=True, key="dash_refresh"):
        st.rerun()

    queue = get_claims_queue(session, ctx.app_role, ctx.username, search, status)
    render_claims_table(queue.head(20), key_prefix="dash")
    render_legend()
    st.markdown("</section>", unsafe_allow_html=True)

    charts = get_dashboard_charts(session, ctx.app_role, ctx.username)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Claims by status")
        if not charts["status"].empty:
            st.bar_chart(charts["status"].set_index("STATUS"))
        st.markdown("#### Claims by priority")
        if not charts["priority"].empty:
            st.bar_chart(charts["priority"].set_index("PRIORITY"))
    with right:
        st.markdown("#### Claims by specialty")
        if not charts["specialty"].empty:
            st.bar_chart(charts["specialty"].set_index("SPECIALTY"))
