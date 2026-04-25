from __future__ import annotations

import streamlit as st

from components.charts import render_series_bar_chart
from services.report_service import get_report_frame


def render(session, ctx) -> None:
    st.markdown("<h1 class='mm-page-title'>Reports & Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<div class='mm-page-subtitle'>Operational and workload insights.</div>", unsafe_allow_html=True)

    df = get_report_frame(session, app_role=ctx.app_role, username=ctx.username)

    if df.empty:
        st.info("No report data available.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<section class='mm-panel'>", unsafe_allow_html=True)
        render_series_bar_chart(df.groupby("STATUS").size(), "Throughput by status")
        render_series_bar_chart(df.groupby("PRIORITY").size(), "Priority mix")
        st.markdown("</section>", unsafe_allow_html=True)
    with c2:
        st.markdown("<section class='mm-panel'>", unsafe_allow_html=True)
        render_series_bar_chart(df.groupby("SPECIALTY").size(), "Specialty mix")
        st.markdown("#### Faculty load")
        load = df.groupby("ASSIGNED_TO").agg(TOTAL=("CLAIM_ID", "count")).reset_index()
        st.dataframe(load, use_container_width=True)
        st.markdown("</section>", unsafe_allow_html=True)
