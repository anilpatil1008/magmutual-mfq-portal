from __future__ import annotations

import streamlit as st

from components.charts import render_bar
from services.report_service import get_report_frames


def render(session, ctx) -> None:
    st.subheader("Reports & Analytics")
    metrics = get_report_frames(session, app_role=ctx.app_role, username=ctx.username)

    if all(frame.empty for frame in metrics.values()):
        st.info("No report data available.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Throughput by status")
        render_bar(metrics["status"], "STATUS")
        st.markdown("#### Priority mix")
        render_bar(metrics["priority"], "PRIORITY")
    with c2:
        st.markdown("#### Specialty mix")
        render_bar(metrics["specialty"], "SPECIALTY")
        st.markdown("#### Faculty load")
        st.dataframe(metrics["faculty"], use_container_width=True)
