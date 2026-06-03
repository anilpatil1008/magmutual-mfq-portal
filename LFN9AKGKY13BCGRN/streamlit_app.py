import streamlit as st

from components.layout import load_css, render_header, render_sidebar
from pages import admin, claim_details, claims, dashboard, reports
from services.notification_service import get_user_notifications
from services.rbac_service import get_available_roles, get_current_user_context, get_selected_sf_role
from services.snowflake_service import get_session
from utils.validate_snowflake_objects import render_missing_objects, validate_required_objects
from config import snowflake_objects as obj

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

required_objects = (
        (obj.MFQ_RECENT_CLAIMS_VIEW, "config/snowflake_objects.py", "Claims/Dashboard"),
        (obj.MFQ_CLAIM_DETAIL_VW, "config/snowflake_objects.py", "Claim Details"),
        (obj.MFQ_NOTIFICATIONS_VIEW, "config/snowflake_objects.py", "Header Notifications"),
        (obj.MFQ_CLAIM_DEFENDANTS_TABLE, "config/snowflake_objects.py", "Claim Details"),
        (obj.MFQ_RECORD_SUMMARY_TABLE, "config/snowflake_objects.py", "Claim Details"),
        (obj.MFQ_MEDCRON_SUMMARY_TABLE, "config/snowflake_objects.py", "Claim Details"),
        (obj.MFQ_LEGAL_MEMO_TABLE, "config/snowflake_objects.py", "Claim Details"),
        (obj.MFQ_DOCUMENTS_TABLE, "config/snowflake_objects.py", "Claim Details"),
        (obj.MFQ_ASSIGNMENT_QUEUE_VIEW, "config/snowflake_objects.py", "Claim Details"),
        (obj.MFQ_STATUS_HISTORY_TABLE, "config/snowflake_objects.py", "Claim Details"),
        (obj.MFQ_SECTION_CONFIDENCE_TABLE, "config/snowflake_objects.py", "Claim Details"),
        (obj.LLM_EVALUATION_TABLE, "config/snowflake_objects.py", "Claim Details"),
 )
missing_objects = validate_required_objects(session, required_objects)
render_missing_objects(missing_objects)

if "active_page" not in st.session_state:
    st.session_state.active_page = "Dashboard"
if "current_view" not in st.session_state:
    st.session_state.current_view = "dashboard"
if "selected_claim_id" not in st.session_state:
    st.session_state.selected_claim_id = None


def _query_param_value(name: str) -> str:
    value = st.query_params.get(name)
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or "").strip()


def _sync_claim_details_route_from_query_params() -> None:
    query_page = _query_param_value("page")
    query_claim_id = _query_param_value("claim_id")
    if query_page.casefold() == "claim details".casefold() and query_claim_id:
        st.session_state["selected_claim_id"] = query_claim_id
        st.session_state["active_page"] = "Claim Details"
        st.session_state["current_view"] = "Claim Details"


_sync_claim_details_route_from_query_params()


page_map = {
    "Dashboard": dashboard.render,
    "Claims": claims.render,
    "Claim Details": claim_details.render,
    "Reports": reports.render,
    "Admin": admin.render,
}

notifications = get_user_notifications(session, ctx.username, limit=6)
render_header(session, ctx, notifications)
render_sidebar(ctx)
_sync_claim_details_route_from_query_params()

render_fn = page_map.get(st.session_state.active_page, dashboard.render)
render_fn(session=session, ctx=ctx)
st.stop()
