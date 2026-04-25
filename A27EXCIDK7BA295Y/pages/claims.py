from __future__ import annotations

import streamlit as st

from components.tables import render_claims_table
from services.claim_service import get_claims_queue, get_status_values


def render(session, ctx) -> None:
    st.markdown("<h1 class='mm-page-title'>Claims</h1>", unsafe_allow_html=True)
    st.markdown("<div class='mm-page-subtitle'>Claims work queue and review actions.</div>", unsafe_allow_html=True)

    st.markdown("<section class='mm-panel'>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns([3, 1.5, 1.3])

    search = f1.text_input("Search", placeholder="Claim ID, Patient, Defendant, File Number")
    status = f2.selectbox("Status", get_status_values(session), index=0)
    sort_by = f3.selectbox("Sort", ["Newest", "Oldest"])

    df = get_claims_queue(session, ctx.app_role, ctx.username, search, status)
    if "DATE_REQUESTED" in df.columns and sort_by == "Oldest":
        df = df.sort_values("DATE_REQUESTED", ascending=True)

    render_claims_table(df, key_prefix="claims")
    st.markdown("</section>", unsafe_allow_html=True)
