import streamlit as st

from components.layout import load_css, render_header, render_sidebar
from pages import admin, claim_details, claims, dashboard, reports
from services.notification_service import get_user_notifications
from services.rbac_service import get_current_user_context
from services.snowflake_service import get_session

st.set_page_config(
    page_title="MagMutual MFQ Enterprise Portal",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()
session = get_session()
ctx = get_current_user_context(session)

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
