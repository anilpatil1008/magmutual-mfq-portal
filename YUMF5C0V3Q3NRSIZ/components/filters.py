import streamlit as st

from utils.constants import CLAIM_STATUSES


def render_claim_filters(prefix: str = ""):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        search = st.text_input("Search (Claim ID / Patient / Defendant)", key=f"{prefix}_search")
    with c2:
        status = st.selectbox("Status", ["All", *CLAIM_STATUSES], key=f"{prefix}_status")
    with c3:
        report_clicked = st.button("Generate Report", key=f"{prefix}_report")
    return search, status, report_clicked
