from __future__ import annotations

import streamlit as st

from components.tables import render_claims_table
from services.claim_service import ClaimService


def render_claims(user_id: str) -> None:
    st.markdown('<div class="claims-page-wrap">', unsafe_allow_html=True)
    st.markdown("""<div class="page-header-block"><div class="page-title">Claims</div><div class="page-subtitle">Select a claim from the work queue to review details.</div></div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    claim_service = ClaimService()
    search_text = st.session_state.get("claims_page_search", "")
    queue_df = claim_service.get_queue(search_text=search_text)

    def on_regenerate(claim_id: str) -> None:
        claim_service.request_regeneration(claim_id, user_id)
        st.success("Regeneration requested")
        st.rerun()

    def on_review(claim_id: str) -> None:
        st.session_state.selected_claim_id = claim_id
        st.session_state.page = "Claim Detail"
        st.rerun()

    render_claims_table(
        queue_df,
        on_regenerate=on_regenerate,
        on_review=on_review,
        show_regenerate=True,
        title="Claims Queue",
        subtitle="Review and manage claims submitted for assessment.",
        search_key="claims_page_search",
    )
