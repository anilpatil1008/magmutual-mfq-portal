from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

from components.notifications import render_notification_center
from services.rbac_service import APP_ROLES, allowed_pages, set_active_role

_HIDE_DEFAULT_STREAMLIT_NAV_CSS = """
<style>
section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {
    display: none !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.75rem !important;
}
</style>
"""


def load_css() -> None:
    css_file = Path(__file__).resolve().parent.parent / "styles" / "carbon_like.css"
    if css_file.exists():
        st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    st.markdown(_HIDE_DEFAULT_STREAMLIT_NAV_CSS, unsafe_allow_html=True)


def _render_role_selector(current_role: str) -> None:
    st.markdown(
        f"""
        <div class="mm-role-pill" aria-hidden="true">
            <span class="mm-role-pill-text">{escape(current_role)}</span>
            <span class="mm-role-pill-chevron">▾</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.popover("Role", use_container_width=True):
        st.markdown("<div class='mm-popover-title'>Switch Role</div>", unsafe_allow_html=True)
        for role in APP_ROLES:
            is_selected = role == current_role
            if st.button(
                f"✓ {role}" if is_selected else role,
                key=f"header_role_option_{role}",
                use_container_width=True,
                type="secondary" if is_selected else "tertiary",
            ):
                if not is_selected:
                    set_active_role(role)
                    st.rerun()


def render_header(ctx, notifications_df) -> None:
    unread = int((~notifications_df["IS_READ"]).sum()) if "IS_READ" in notifications_df.columns else 0

    username_display = str(ctx.username).replace("_", " ").strip()
    full_name = " ".join(part.capitalize() for part in username_display.split()) or "Unknown User"
    initials = "".join(part[0] for part in full_name.split()[:2]).upper() or "U"
    safe_full_name = escape(full_name)
    safe_username = escape(str(ctx.username))
    email = f"{str(ctx.username).lower().replace(' ', '.')}@magmutual.com"

    st.markdown("<section class='mm-topbar'>", unsafe_allow_html=True)
    left_col, right_col = st.columns([2.8, 2.2], gap="small")

    with left_col:
        st.markdown("<div class='mm-topbar-search-wrap'>", unsafe_allow_html=True)
        st.text_input(
            "Search",
            placeholder="Search claims, files, or patients...",
            label_visibility="collapsed",
            key="topbar_search_query",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("<div class='mm-header-right'>", unsafe_allow_html=True)

        role_col, bell_col, profile_col = st.columns([1.15, 0.55, 1.55], gap="small")

        with role_col:
            st.markdown("<div class='mm-header-item mm-header-item-role'>", unsafe_allow_html=True)
            _render_role_selector(ctx.app_role)
            st.markdown("</div>", unsafe_allow_html=True)

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
                <div class="mm-profile-pill" aria-hidden="true">
                    <span class="mm-avatar">{escape(initials)}</span>
                    <span class="mm-profile-name">{safe_full_name}</span>
                    <span class="mm-profile-arrow">▾</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.popover("Profile", use_container_width=True):
                st.markdown(
                    f"""
                    <div class="mm-profile-card">
                        <div class="mm-profile-card-head">
                            <span class="mm-avatar mm-avatar-lg">{escape(initials)}</span>
                            <div class="mm-profile-meta">
                                <div class="mm-profile-fullname">{safe_full_name}</div>
                                <div class="mm-profile-email">{escape(email)}</div>
                                <div class="mm-profile-role">{escape(ctx.app_role)}</div>
                            </div>
                        </div>
                        <div class="mm-profile-divider"></div>
                        <div class="mm-profile-signout">↪ Sign out</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption(f"User ID: {safe_username}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</section>", unsafe_allow_html=True)


def render_sidebar(ctx) -> None:
    username_display = str(ctx.username).replace("_", " ").strip()
    full_name = " ".join(part.capitalize() for part in username_display.split()) or "Unknown User"
    initials = "".join(part[0] for part in full_name.split()[:2]).upper() or "U"

    page_icons = {
        "Dashboard": "⌗",
        "Claims": "📄",
        "Claim Details": "🗂",
        "Reports": "📊",
        "Admin": "⚙",
    }

    with st.sidebar:
        st.markdown("<div class='mm-sidebar-brand'>● MagMutual</div>", unsafe_allow_html=True)
        st.markdown("<div class='mm-sidebar-title'>Navigation</div>", unsafe_allow_html=True)

        pages = allowed_pages(ctx.app_role)
        for page in pages:
            active = st.session_state.active_page == page
            icon = page_icons.get(page, "•")
            label = f"{icon}  {page}"
            if st.button(label, use_container_width=True, key=f"nav_{page}", type="primary" if active else "secondary"):
                st.session_state.active_page = page
                st.rerun()

        st.markdown("<div class='mm-sidebar-spacer'></div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class='mm-sidebar-user'>
                <span class='mm-avatar'>{escape(initials)}</span>
                <div class='mm-sidebar-user-meta'>
                    <div class='mm-sidebar-user-name'>{escape(full_name)}</div>
                    <div class='mm-sidebar-user-role'>{escape(ctx.app_role)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get("selected_claim_id"):
            st.caption(f"Selected claim: {st.session_state.selected_claim_id}")
