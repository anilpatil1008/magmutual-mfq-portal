import streamlit as st

from components.layout import load_css, render_header, render_sidebar
from pages import admin, claim_details, claims, dashboard, reports
from services.notification_service import get_user_notifications
from services.rbac_service import get_available_roles, get_current_user_context, get_selected_sf_role
from services.snowflake_service import get_session
from utils.navigation import (
    CLAIM_DETAILS_PAGE,
    CLAIM_DETAILS_VIEW,
    DASHBOARD_PAGE,
    DASHBOARD_VIEW,
    is_claim_details_route_active,
    navigate_to_claim_details,
    navigate_to_dashboard,
)

st.set_page_config(
    page_title="MagMutual MFQ Enterprise Portal",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()
session = get_session()
available_roles, current_sf_role = get_available_roles(session)
st.session_state["available_roles"] = available_roles
selected_sf_role = get_selected_sf_role(session)
st.session_state["selected_sf_role"] = selected_sf_role

ctx = get_current_user_context(session)

if "active_page" not in st.session_state:
    st.session_state.active_page = DASHBOARD_PAGE
if "current_view" not in st.session_state:
    st.session_state.current_view = DASHBOARD_VIEW
if "selected_claim_id" not in st.session_state:
    st.session_state.selected_claim_id = None
if "active_sidebar_item" not in st.session_state:
    st.session_state.active_sidebar_item = st.session_state.active_page


def _query_param_value(name: str) -> str:
    value = st.query_params.get(name)
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "").strip()


def _sync_claim_details_route_from_query_params() -> None:
    query_page = _query_param_value("page")
    query_claim_id = _query_param_value("claim_id")
    if query_page.casefold() == CLAIM_DETAILS_PAGE.casefold() and query_claim_id:
        navigate_to_claim_details(query_claim_id)


def _normalize_navigation_state() -> None:
    """Keep detail/dashboard session keys aligned before rendering a page."""
    current_view = str(st.session_state.get("current_view") or DASHBOARD_VIEW).strip().lower()
    active_page = str(st.session_state.get("active_page") or DASHBOARD_PAGE).strip()
    selected_claim_id = str(st.session_state.get("selected_claim_id") or "").strip()

    if current_view == CLAIM_DETAILS_VIEW and selected_claim_id:
        navigate_to_claim_details(selected_claim_id)
        return

    if current_view == CLAIM_DETAILS_VIEW and not selected_claim_id:
        navigate_to_dashboard()
        st.query_params.clear()
        return

    if active_page == CLAIM_DETAILS_PAGE and current_view != CLAIM_DETAILS_VIEW:
        navigate_to_dashboard()
        st.query_params.clear()
        return

    if active_page not in {DASHBOARD_PAGE, "Claims", "Reports", "Admin"}:
        navigate_to_dashboard()
        st.query_params.clear()
        return

    if active_page == DASHBOARD_PAGE or current_view == DASHBOARD_VIEW:
        st.session_state["active_page"] = DASHBOARD_PAGE
        st.session_state["current_view"] = DASHBOARD_VIEW
        st.session_state["active_sidebar_item"] = DASHBOARD_PAGE


_sync_claim_details_route_from_query_params()
_normalize_navigation_state()

notifications = get_user_notifications(session, ctx.username, limit=6)
render_header(session, ctx, notifications)
render_sidebar(ctx)
_sync_claim_details_route_from_query_params()
_normalize_navigation_state()

if is_claim_details_route_active():
    claim_details.render(session=session, ctx=ctx)
elif st.session_state.get("active_page") == "Claims":
    claims.render(session=session, ctx=ctx)
elif st.session_state.get("active_page") == "Reports":
    reports.render(session=session, ctx=ctx)
elif st.session_state.get("active_page") == "Admin":
    admin.render(session=session, ctx=ctx)
else:
    navigate_to_dashboard()
    dashboard.render(session=session, ctx=ctx)
st.stop()
