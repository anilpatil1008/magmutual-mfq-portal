from __future__ import annotations

import logging

import streamlit as st

from components.tables import render_claims_table
from services.claim_service import get_claims_queue, get_status_values
from services.rbac_service import get_session_context_snapshot

logger = logging.getLogger(__name__)


def render(session, ctx) -> None:
    st.subheader("Claims Work Queue")

    if "claims_search_text" not in st.session_state:
        st.session_state["claims_search_text"] = ""
    if "claims_status_filter" not in st.session_state:
        st.session_state["claims_status_filter"] = "All"
    if "claims_sort_order" not in st.session_state:
        st.session_state["claims_sort_order"] = "Newest"

    f1, f2, f3 = st.columns([3, 2, 2])
    with f1:
        search = st.text_input(
            "Search",
            placeholder="Claim ID, Patient, Defendant, File Number",
            key="claims_search_text",
        )
    with f2:
        statuses = get_status_values(session)
        current_status = st.session_state.get("claims_status_filter", "All")
        status_index = statuses.index(current_status) if current_status in statuses else 0
        status = st.selectbox("Status", statuses, index=status_index, key="claims_status_filter")
    with f3:
        sort_by = st.selectbox("Sort", ["Newest", "Oldest"], key="claims_sort_order")

    session_ctx = get_session_context_snapshot(session)
    session_ctx["selected_sf_role"] = str(st.session_state.get("selected_sf_role") or "")
    logger.info("claims_session_context=%s", session_ctx)

    df = get_claims_queue(session, ctx.username, search, status)
    logger.info("claims_query_row_count=%d", len(df))
    if "DATE_REQUESTED" in df.columns and sort_by == "Oldest":
        df = df.sort_values("DATE_REQUESTED", ascending=True)

    render_claims_table(df, key_prefix="claims")
