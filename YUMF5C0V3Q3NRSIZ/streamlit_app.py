import streamlit as st

from components.layout import close_shell, load_css, render_shell
from pages import admin, claim_details, claims, dashboard, reports
from services.snowflake_service import get_session
from utils.helpers import init_state

st.set_page_config(page_title="MagMutual MFQ Portal", layout="wide")
init_state()
load_css()

session = get_session()
username = session.sql("SELECT CURRENT_USER() AS USERNAME").to_pandas().iloc[0]["USERNAME"]
role = render_shell(username)

page = st.session_state.active_page
if page == "Dashboard":
    dashboard.render(session, role, username)
elif page == "Claims":
    claims.render(session, role, username)
elif page == "Claim Details":
    claim_details.render(session, role, username, st.session_state.selected_claim_id)
elif page == "Admin / RBAC":
    admin.render(session, role, username)
else:
    reports.render(session, role, username)

close_shell()
