from __future__ import annotations

import streamlit as st

DASHBOARD_PAGE = "Dashboard"
CLAIM_DETAILS_PAGE = "Claim Details"
DASHBOARD_VIEW = "dashboard"
CLAIM_DETAILS_VIEW = "claim_details"


def navigate_to_dashboard() -> None:
    """Synchronize all session navigation keys for the Dashboard route."""
    st.session_state["active_page"] = DASHBOARD_PAGE
    st.session_state["current_view"] = DASHBOARD_VIEW
    st.session_state["active_sidebar_item"] = DASHBOARD_PAGE
    st.session_state["selected_claim_id"] = None
    st.session_state["selected_claim"] = None
    st.session_state["claim_detail_view"] = False
    st.session_state["show_claim_details_nav"] = False
    st.session_state["page"] = DASHBOARD_PAGE


def navigate_to_claim_details(claim_id: str) -> None:
    """Synchronize all session navigation keys for the Claim Details route."""
    normalized_claim_id = str(claim_id or "").strip()
    if not normalized_claim_id:
        navigate_to_dashboard()
        return

    st.session_state["selected_claim_id"] = normalized_claim_id
    st.session_state["selected_claim"] = None
    st.session_state["active_page"] = CLAIM_DETAILS_PAGE
    st.session_state["current_view"] = CLAIM_DETAILS_VIEW
    st.session_state["active_sidebar_item"] = CLAIM_DETAILS_PAGE
    st.session_state["claim_detail_view"] = True
    st.session_state["show_claim_details_nav"] = True
    st.session_state["page"] = CLAIM_DETAILS_PAGE


def is_claim_details_route_active() -> bool:
    """Return True only when both the route and selected claim explicitly point to Claim Details."""
    current_view = str(st.session_state.get("current_view") or "").strip().lower()
    selected_claim_id = str(st.session_state.get("selected_claim_id") or "").strip()
    return current_view == CLAIM_DETAILS_VIEW and bool(selected_claim_id)


def should_show_claim_details_nav() -> bool:
    """Return True only while the user is actively viewing a selected claim."""
    return bool(st.session_state.get("show_claim_details_nav")) and is_claim_details_route_active()
