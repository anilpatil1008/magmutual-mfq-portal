from __future__ import annotations

import streamlit as st

DASHBOARD_PAGE = "Dashboard"
REPORTS_PAGE = "Reports"
CLAIM_DETAILS_PAGE = "Claim Details"
DASHBOARD_VIEW = "dashboard"
REPORTS_VIEW = "reports"
CLAIM_DETAILS_VIEW = "claim_details"


def navigate_to_dashboard() -> None:
    """Synchronize session state for the Dashboard route."""
    st.session_state["selected_claim_id"] = None
    st.session_state["selected_claim"] = None
    st.session_state["current_view"] = DASHBOARD_VIEW
    st.session_state["active_page"] = DASHBOARD_PAGE
    st.session_state["claim_detail_view"] = False
    st.session_state["page"] = DASHBOARD_PAGE


def navigate_to_reports() -> None:
    """Synchronize session state for the Reports route."""
    st.session_state["selected_claim_id"] = None
    st.session_state["selected_claim"] = None
    st.session_state["current_view"] = REPORTS_VIEW
    st.session_state["active_page"] = REPORTS_PAGE
    st.session_state["claim_detail_view"] = False
    st.session_state["page"] = REPORTS_PAGE


def navigate_to_claim_details(claim_id: str) -> None:
    """Synchronize session state for the temporary Claim Details route."""
    normalized_claim_id = str(claim_id or "").strip()
    if not normalized_claim_id:
        navigate_to_dashboard()
        return

    st.session_state["selected_claim_id"] = normalized_claim_id
    st.session_state["selected_claim"] = None
    st.session_state["current_view"] = CLAIM_DETAILS_VIEW
    st.session_state["active_page"] = CLAIM_DETAILS_PAGE
    st.session_state["claim_detail_view"] = True
    st.session_state["page"] = CLAIM_DETAILS_PAGE


def is_claim_details_route_active() -> bool:
    """Return True only when the current view explicitly points to a selected claim."""
    current_view = str(st.session_state.get("current_view") or "").strip().lower()
    selected_claim_id = str(st.session_state.get("selected_claim_id") or "").strip()
    return current_view == CLAIM_DETAILS_VIEW and bool(selected_claim_id)
