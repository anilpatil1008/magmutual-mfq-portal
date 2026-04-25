from __future__ import annotations

from html import escape
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


def _render_role_selector(current_role: str) -> None:
    available_roles = st.session_state.get("available_roles", APP_ROLES)
    role_options = [str(role) for role in available_roles if str(role).strip()]
    if current_role not in role_options:
        role_options = [current_role, *role_options]

    selected_role = st.selectbox(
        "Role",
        role_options,
        index=role_options.index(current_role),
        key="header_role_select",
        label_visibility="collapsed",
    )

    if selected_role != current_role:
        set_active_role(selected_role)
        st.rerun()


def render_header(ctx, notifications_df) -> None:
    unread = int((~notifications_df["IS_READ"]).sum()) if "IS_READ" in notifications_df.columns else 0

    username_display = str(ctx.username).replace("_", " ").strip()
    full_name = " ".join(part.capitalize() for part in username_display.split()) or "Unknown User"
    initials = "".join(part[0] for part in full_name.split()[:2]).upper() or "U"
    safe_full_name = escape(full_name)
    safe_username = escape(str(ctx.username))
    email = f"{str(ctx.username).lower().replace(' ', '.')}@magmutual.com"

    header_container = st.container(key="mm_header_controls")
    spacer_col, role_col, bell_col, profile_col = header_container.columns([6.0, 2.5, 1.1, 3.2], gap="small")

    with spacer_col:
        st.empty()

    with role_col:
        st.markdown("<div class='mm-header-item mm-header-item-role'>", unsafe_allow_html=True)
        _render_role_selector(ctx.app_role)
        st.markdown("</div>", unsafe_allow_html=True)

    with bell_col:
        st.markdown("<div class='mm-header-item mm-header-item-bell'>", unsafe_allow_html=True)
        with st.popover(f"🔔 {unread}", use_container_width=True, key="header_notifications_popover"):
            render_notification_center(notifications_df)
        st.markdown("</div>", unsafe_allow_html=True)

    with profile_col:
        st.markdown("<div class='mm-header-item mm-header-item-profile'>", unsafe_allow_html=True)
        with st.popover(
            f"{initials}  {full_name} ▾",
            use_container_width=True,
            key="header_profile_popover",
        ):
            st.markdown(
                f"""
                <div class="mm-profile-card">
                    <div class="mm-profile-card-head">
                        <span class="mm-avatar mm-avatar-lg">{escape(initials)}</span>
                        <div class="mm-profile-meta">
                            <div class="mm-profile-fullname">{safe_full_name}</div>
                            <div class="mm-profile-email">{escape(email)}</div>
                            <div class="mm-profile-role">{escape(ctx.app_role)} • {escape(ctx.sf_role)}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(f"User ID: {safe_username}")
        st.markdown("</div>", unsafe_allow_html=True)


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
