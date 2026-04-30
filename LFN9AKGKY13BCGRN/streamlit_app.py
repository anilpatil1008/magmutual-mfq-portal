import streamlit as st

from components.layout import load_css, render_header, render_sidebar
from pages import admin, claim_details, claims, dashboard, reports
from services.notification_service import get_user_notifications
from services.rbac_service import get_current_user_context
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
ctx = get_current_user_context(session)

required_objects = (
        (obj.MFQ_RECENT_CLAIMS_VIEW, "config/snowflake_objects.py", "Claims/Dashboard"),
        (obj.MFQ_CLAIM_DETAIL_VIEW, "config/snowflake_objects.py", "Claim Details"),
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
if "selected_claim_id" not in st.session_state:
    st.session_state.selected_claim_id = None

query_page = st.query_params.get("page")
query_claim_id = st.query_params.get("claim_id")
if query_page == "Claim Details" and query_claim_id:
    st.session_state.active_page = "Claim Details"
    st.session_state.selected_claim_id = str(query_claim_id).strip()
    st.query_params.clear()


page_map = {
    "Dashboard": dashboard.render,
    "Claims": claims.render,
    "Claim Details": claim_details.render,
    "Reports": reports.render,
    "Admin": admin.render,
}

render_fn = page_map.get(st.session_state.active_page, dashboard.render)

# Skip header/sidebar notification fetch work for in-dashboard claim details fast path
is_dashboard_claim_details = (
    st.session_state.get("active_page") == "Dashboard"
    and st.session_state.get("current_view") == "claim_details"
    and st.session_state.get("selected_claim_id")
)

if not is_dashboard_claim_details:
    notifications = get_user_notifications(session, ctx.username, limit=6)
    render_header(ctx, notifications)
    render_sidebar(ctx)

render_fn(session=session, ctx=ctx)
st.stop()
