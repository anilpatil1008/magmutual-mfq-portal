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

missing_objects = validate_required_objects(session, [
    {"object_name": obj.MFQ_RECENT_CLAIMS_VIEW, "expected_location": "config/snowflake_objects.py", "page": "Claims/Dashboard"},
    {"object_name": obj.MFQ_CLAIM_DETAIL_VIEW, "expected_location": "config/snowflake_objects.py", "page": "Claim Details"},
    {"object_name": obj.MFQ_NOTIFICATIONS_VIEW, "expected_location": "config/snowflake_objects.py", "page": "Header Notifications"},
])
render_missing_objects(missing_objects)

if "active_page" not in st.session_state:
    st.session_state.active_page = "Dashboard"
if "selected_claim_id" not in st.session_state:
    st.session_state.selected_claim_id = None

notifications = get_user_notifications(session, ctx.username, limit=6)
render_header(ctx, notifications)
render_sidebar(ctx)

page_map = {
    "Dashboard": dashboard.render,
    "Claims": claims.render,
    "Claim Details": claim_details.render,
    "Reports": reports.render,
    "Admin": admin.render,
}

render_fn = page_map.get(st.session_state.active_page, dashboard.render)
render_fn(session=session, ctx=ctx)
