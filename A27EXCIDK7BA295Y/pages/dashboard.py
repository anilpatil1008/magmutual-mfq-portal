from __future__ import annotations

import streamlit as st

from components.badges import render_legend
from components.cards import render_kpi_cards
from components.tables import render_claims_table
from services.claim_service import get_claims_queue, get_status_values
from services.dashboard_service import get_dashboard_charts, get_dashboard_metrics


def render(session, ctx) -> None:
    st.subheader("Role Dashboard")

    metrics = get_dashboard_metrics(session, app_role=ctx.app_role, username=ctx.username)
    render_kpi_cards(metrics)
    render_legend()

    c1, c2, c3 = st.columns([3, 2, 1])
    search = c1.text_input("Search claims, patient, defendant, or file")
    status = c2.selectbox("Status", get_status_values(session), index=0)
    c3.write("")
    if c3.button("Refresh", use_container_width=True):
        st.rerun()

    queue = get_claims_queue(session, ctx.app_role, ctx.username, search, status)
    st.markdown("#### Recent claim queue")
    render_claims_table(queue.head(20), key_prefix="dash")

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
