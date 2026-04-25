from __future__ import annotations

import pandas as pd
import streamlit as st

from components.badges import priority_badge, status_badge

VISIBLE_COLUMNS = [
    "CLAIM_ID",
    "PATIENT_NAME",
    "DEFENDANT_NAME",
    "STATUS",
    "PRIORITY",
    "DATE_REQUESTED",
]


def render_claims_table(df: pd.DataFrame, key_prefix: str = "claims") -> None:
    if df.empty:
        st.info("No claims found for this filter context.")
        return

    show_df = df.copy()
    show_df = show_df[[c for c in VISIBLE_COLUMNS if c in show_df.columns]]

    st.markdown("<div class='mm-table-wrap'>", unsafe_allow_html=True)

    hcols = st.columns([1.1, 1.95, 1.1, 0.9, 1.1, 0.7], gap="small")
    headers = ["FILE NUMBER", "PATIENT / DEFENDANT", "STATUS", "PRIORITY", "DATE REQUESTED", "ACTION"]
    for col, header in zip(hcols, headers):
        col.markdown(f"<div class='mm-table-head-cell'>{header}</div>", unsafe_allow_html=True)

    for _, row in show_df.iterrows():
        claim_id = str(row.get("CLAIM_ID", ""))
        patient = str(row.get("PATIENT_NAME", "-"))
        defendant = str(row.get("DEFENDANT_NAME", "-"))
        status = status_badge(str(row.get("STATUS", "-")))
        priority = priority_badge(str(row.get("PRIORITY", "-")))
        date_requested = str(row.get("DATE_REQUESTED", "-"))

        cols = st.columns([1.1, 1.95, 1.1, 0.9, 1.1, 0.7], gap="small")
        cols[0].markdown(f"<div class='mm-table-cell mm-table-file'>{claim_id}</div>", unsafe_allow_html=True)
        cols[1].markdown(
            f"<div class='mm-table-cell'><div class='mm-table-patient'>{patient}</div><div class='mm-table-defendant'>vs. {defendant}</div></div>",
            unsafe_allow_html=True,
        )
        cols[2].markdown(f"<div class='mm-table-cell'>{status}</div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div class='mm-table-cell'>{priority}</div>", unsafe_allow_html=True)
        cols[4].markdown(f"<div class='mm-table-cell'>{date_requested}</div>", unsafe_allow_html=True)
        if cols[5].button("Review →", key=f"{key_prefix}_open_{claim_id}", use_container_width=True, type="tertiary"):
            st.session_state.selected_claim_id = claim_id
            st.session_state.active_page = "Claim Details"
            st.rerun()
        st.markdown("<div class='mm-table-row-divider'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
