from __future__ import annotations

from pathlib import Path

import streamlit as st

from components.notifications import render_notification_center
from services.rbac_service import APP_ROLES, allowed_pages, set_active_role


def load_css() -> None:
    css_file = Path(__file__).resolve().parent.parent / "styles" / "carbon_like.css"
    if css_file.exists():
        st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_header(ctx, notifications_df) -> None:
    unread = int((~notifications_df["IS_READ"]).sum()) if "IS_READ" in notifications_df.columns else 0
    st.markdown(
        f"""
        <section class="mm-header">
            <div>
                <h1>MagMutual MFQ Enterprise Portal</h1>
                <p>Workflow-ready claim intelligence and medical faculty collaboration.</p>
            </div>
            <div class="mm-header-meta">
                <span class="mm-chip">User: {ctx.username}</span>
                <span class="mm-chip">Role: {ctx.app_role}</span>
                <span class="mm-chip">Snowflake Role: {ctx.sf_role}</span>
                <span class="mm-chip mm-notif-chip">Unread: {unread}</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Notifications", expanded=False):
        render_notification_center(notifications_df)


def render_sidebar(ctx) -> None:
    with st.sidebar:
        st.markdown("### MagMutual")
        role = st.selectbox("Application role", APP_ROLES, index=APP_ROLES.index(ctx.app_role))
        if role != ctx.app_role:
            set_active_role(role)
            st.rerun()

        pages = allowed_pages(role)
        st.markdown("---")
        for page in pages:
            active = st.session_state.active_page == page
            label = f"{'●' if active else '○'} {page}"
            if st.button(label, use_container_width=True, key=f"nav_{page}"):
                st.session_state.active_page = page
                st.rerun()

        if st.session_state.get("selected_claim_id"):
            st.caption(f"Selected claim: {st.session_state.selected_claim_id}")
