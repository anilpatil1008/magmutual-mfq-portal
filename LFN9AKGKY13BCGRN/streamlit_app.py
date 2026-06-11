import streamlit as st
from utils.streamlit_compat import is_debug_enabled, safe_child_container, safe_container, safe_set_page_config

from components.layout import load_css, render_header, render_sidebar
from pages import claim_details, dashboard, reports
from services.notification_service import get_user_notifications
from services.rbac_service import get_available_roles, get_current_user_context, get_selected_sf_role
from services.snowflake_context import render_role_debug_expander
from services.snowflake_service import get_session
from core.snowflake_session import is_active_session_available
from utils.navigation import (
    CLAIM_DETAILS_PAGE,
    CLAIM_DETAILS_VIEW,
    DASHBOARD_PAGE,
    DASHBOARD_VIEW,
    REPORTS_VIEW,
    navigate_to_claim_details,
    set_dashboard_route,
    set_reports_route,
)

safe_set_page_config(
    page_title="MagMutual MFQ Enterprise Portal",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()
session = get_session()
available_roles, current_sf_role = get_available_roles(session)
st.session_state["available_roles"] = available_roles
st.session_state["viewer_granted_roles"] = available_roles
st.session_state["runtime_owner_role"] = current_sf_role or "Unknown"
selected_sf_role = get_selected_sf_role(session)
st.session_state["selected_app_role"] = selected_sf_role
st.session_state["selected_sf_role"] = selected_sf_role

ctx = get_current_user_context(session)

if is_debug_enabled():
    st.caption(
        f"Debug: Streamlit {st.__version__} | "
        f"active Snowflake session: {is_active_session_available()}"
    )

render_role_debug_expander(session)

if "active_page" not in st.session_state:
    st.session_state.active_page = DASHBOARD_PAGE
if "current_view" not in st.session_state:
    st.session_state.current_view = DASHBOARD_VIEW
if "selected_claim_id" not in st.session_state:
    st.session_state.selected_claim_id = None
if "show_claim_details_nav" not in st.session_state:
    st.session_state.show_claim_details_nav = False


def _query_param_value(name: str) -> str:
    value = st.query_params.get(name)
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "").strip()


def _sync_claim_details_route_from_query_params() -> None:
    """Honor explicit Claim Details deep links once before routing.

    The query string is treated as a one-time navigation intent so a later
    Back to Dashboard action cannot be undone by a stale ``claim_id`` URL.
    """
    query_page = _query_param_value("page")
    query_claim_id = _query_param_value("claim_id")
    query_route_token = (
        f"{query_page.casefold()}:{query_claim_id}"
        if query_page.casefold() == CLAIM_DETAILS_PAGE.casefold() and query_claim_id
        else ""
    )
    if not query_route_token:
        st.session_state["last_consumed_claim_details_query"] = ""
        return

    if st.session_state.get("last_consumed_claim_details_query") == query_route_token:
        return

    st.session_state["last_consumed_claim_details_query"] = query_route_token
    navigate_to_claim_details(query_claim_id)



def _normalize_navigation_state() -> None:
    """Normalize legacy state without rendering or rerunning.

    ``current_view`` is the only router selector. A stale ``selected_claim_id``
    must not route by itself, and an incomplete Claim Details route is folded
    back to Dashboard before any page body is rendered.
    """
    current_view = str(st.session_state.get("current_view") or DASHBOARD_VIEW).strip().lower()
    selected_claim_id = str(st.session_state.get("selected_claim_id") or "").strip()

    if current_view == CLAIM_DETAILS_VIEW and selected_claim_id:
        st.session_state["current_view"] = CLAIM_DETAILS_VIEW
        st.session_state["selected_claim_id"] = selected_claim_id
        st.session_state["active_page"] = CLAIM_DETAILS_PAGE
        st.session_state["show_claim_details_nav"] = True
        st.session_state["claim_detail_view"] = True
        return

    if current_view == REPORTS_VIEW:
        set_reports_route()
        return

    set_dashboard_route()


_sync_claim_details_route_from_query_params()
_normalize_navigation_state()

notifications = get_user_notifications(session, ctx.username, limit=6)
render_header(session, ctx, notifications)
render_sidebar(ctx)

current_view = str(st.session_state.get("current_view") or DASHBOARD_VIEW).strip().lower()
selected_claim_id = str(st.session_state.get("selected_claim_id") or "").strip()

# Keep the routed page body in a single replaceable slot.  This prevents stale
# Dashboard elements (especially custom-component iframes from Recent Claims)
# from remaining mounted when Review navigates to Claim Details and then back
# to Dashboard in the same browser session.
with safe_container(key="app_main_content"):
    active_view_slot = st.empty()
    with safe_child_container(active_view_slot, key=f"active_view_{current_view}"):
        if current_view == CLAIM_DETAILS_VIEW and selected_claim_id:
            claim_details.render(session=session, ctx=ctx)
            st.stop()

        if current_view == REPORTS_VIEW:
            reports.render(session=session, ctx=ctx)
            st.stop()

        dashboard.render(session=session, ctx=ctx)
        st.stop()
