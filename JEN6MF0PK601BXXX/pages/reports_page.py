from __future__ import annotations

import streamlit as st

from services.claim_service import ClaimService


def render_reports() -> None:
    st.markdown("""<div class="page-title">Reports</div>""", unsafe_allow_html=True)
    st.markdown("""<div class="page-subtitle">Operational KPIs and analytics.</div>""", unsafe_allow_html=True)

    claim_service = ClaimService()
    queue_df = claim_service.get_queue()
    if not queue_df.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Claims by Status")
            st.bar_chart(queue_df["STATUS"].value_counts())
        with c2:
            st.subheader("Claims by Priority")
            st.bar_chart(queue_df["PRIORITY"].value_counts())
