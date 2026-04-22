from __future__ import annotations

import streamlit as st

from config.settings import CONFIG
from components.layout import render_sidebar, render_topbar
from pages.dashboard_page import render_dashboard
from pages.claim_detail_page import render_claim_detail_page
from repositories.notification_repository import get_notifications
from repositories.user_repository import get_user_profile, get_user_roles
from styles.theme import inject_theme


st.set_page_config(
    page_title="MagMutual MFQ Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

if "user_id" not in st.session_state:
    st.session_state.user_id = CONFIG.default_user_id

if "role_key" not in st.session_state:
    st.session_state.role_key = "CLAIMS_ANALYST"

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "selected_claim_id" not in st.session_state:
    st.session_state.selected_claim_id = None

if "claim_detail_tab" not in st.session_state:
    st.session_state.claim_detail_tab = "MFQ Form"

user_profile = get_user_profile(st.session_state.user_id)
roles_df = get_user_roles(st.session_state.user_id)

current_profile = user_profile.iloc[0] if not user_profile.empty else None
display_name = current_profile["DISPLAY_NAME"] if current_profile is not None else "User"
email = current_profile["EMAIL"] if current_profile is not None else "user@example.com"

role_options = roles_df["ROLE_KEY"].tolist() if not roles_df.empty else ["CLAIMS_ANALYST"]
notif_df = get_notifications(st.session_state.user_id)

render_sidebar(st.session_state.role_key)
render_topbar(
    display_name=display_name,
    email=email,
    role_options=role_options,
    current_role=st.session_state.role_key,
    notif_df=notif_df,
)

if st.session_state.page == "Dashboard":
    render_dashboard(display_name, st.session_state.user_id)

elif st.session_state.page == "Claims":
    st.title("Claims")
    st.write("Hook your claims page here.")

elif st.session_state.page == "Claim Detail":
    render_claim_detail_page(
        user_id=st.session_state.user_id,
        role_key=st.session_state.role_key,
    )

elif st.session_state.page == "Reports":
    st.title("Reports")
    st.write("Hook your reports page here.")

elif st.session_state.page == "Admin":
    st.title("Admin")
    st.write("Hook your admin page here.")