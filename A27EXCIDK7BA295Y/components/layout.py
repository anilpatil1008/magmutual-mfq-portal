from __future__ import annotations

from pathlib import Path

import streamlit as st

from components.notifications import render_notification_center
from services.rbac_service import APP_ROLES, allowed_pages, set_active_role

_HIDE_DEFAULT_STREAMLIT_NAV_CSS = """
<style>
/* Hide Streamlit's default multipage sidebar navigation. */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {
    display: none !important;
}

/* Remove extra top spacing reserved for the hidden nav block. */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem !important;
}
</style>
"""


def load_css() -> None:
    css_file = Path(__file__).resolve().parent.parent / "styles" / "carbon_like.css"
    if css_file.exists():
        st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    st.markdown(_HIDE_DEFAULT_STREAMLIT_NAV_CSS, unsafe_allow_html=True)


def render_header(ctx, notifications_df) -> None:
    unread = int((~notifications_df["IS_READ"]).sum()) if "IS_READ" in notifications_df.columns else 0
    initials = "".join(part[0] for part in str(ctx.username).replace("_", " ").split()[:2]).upper() or "U"

    st.markdown("<section class='mm-header'>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1.35, 1], gap="small")

    with left_col:
        st.markdown(
            """
            <div class="mm-header-brand">
                <h1>MagMutual MFQ Enterprise Portal</h1>
                <p>Workflow-ready claim intelligence and medical faculty collaboration.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        role_col, bell_col, profile_col = st.columns([1.45, 0.7, 1.75], gap="small")

        with role_col:
            st.markdown("<div class='mm-header-item mm-header-item-role'>", unsafe_allow_html=True)
            st.markdown("<div class='mm-role-icon' aria-hidden='true'>🛡️</div>", unsafe_allow_html=True)
            role = st.selectbox(
                "Role",
                APP_ROLES,
                index=APP_ROLES.index(ctx.app_role),
                key="header_role_select",
                label_visibility="collapsed",
            )
            st.markdown("</div>", unsafe_allow_html=True)
            if role != ctx.app_role:
                set_active_role(role)
                st.rerun()

        with bell_col:
            st.markdown("<div class='mm-header-item mm-header-item-bell'>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class='mm-bell-badge-wrap' aria-hidden='true'>
                    <span class='mm-bell-icon'>🔔</span>
                    <span class='mm-bell-badge'>{unread}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.popover("Notifications", use_container_width=True):
                render_notification_center(notifications_df)
            st.markdown("</div>", unsafe_allow_html=True)

        with profile_col:
            st.markdown("<div class='mm-header-item mm-header-item-profile'>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="mm-profile-pill">
                    <span class="mm-avatar">{initials}</span>
                    <span class="mm-profile-name">{ctx.username}</span>
                    <span class="mm-profile-arrow">▾</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.popover("Profile", use_container_width=True):
                st.caption(f"User: {ctx.username}")
                st.caption(f"App role: {ctx.app_role}")
                st.caption(f"Snowflake role: {ctx.sf_role}")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</section>", unsafe_allow_html=True)


def render_sidebar(ctx) -> None:
    with st.sidebar:
        st.markdown("### MagMutual")

        pages = allowed_pages(ctx.app_role)
        st.markdown("---")
        for page in pages:
            active = st.session_state.active_page == page
            label = f"{'●' if active else '○'} {page}"
            if st.button(label, use_container_width=True, key=f"nav_{page}"):
                st.session_state.active_page = page
                st.rerun()

        if st.session_state.get("selected_claim_id"):
            st.caption(f"Selected claim: {st.session_state.selected_claim_id}")
