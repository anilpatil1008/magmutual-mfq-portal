from __future__ import annotations

import streamlit as st

from services.claim_service import get_claims_queue


def render(session, ctx) -> None:
    st.subheader("Reports & Analytics")
    df = get_claims_queue(session, app_role=ctx.app_role, username=ctx.username)

    if df.empty:
        st.info("No report data available.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Throughput by status")
        st.bar_chart(df.groupby("STATUS").size())
        st.markdown("#### Priority mix")
        st.bar_chart(df.groupby("PRIORITY").size())
    with c2:
        st.markdown("#### Specialty mix")
        st.bar_chart(df.groupby("SPECIALTY").size())
        st.markdown("#### Faculty load")
        load = df.groupby("ASSIGNED_TO").agg(TOTAL=("CLAIM_ID", "count")).reset_index()
        st.dataframe(load, use_container_width=True)
