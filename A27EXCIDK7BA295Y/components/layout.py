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

    header_container = st.container(key="app_topbar")
    st.markdown(
        """
        <div class="mm-topbar-shell">
            <div class="mm-topbar-title-wrap">
                <div class="mm-topbar-eyebrow">MagMutual Portal</div>
                <div class="mm-topbar-title">Medical Faculty Questionnaire</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    title_col, role_col, bell_col, profile_col = header_container.columns([4.5, 2.2, 1.0, 2.6], gap="small")

    with title_col:
        st.markdown("", unsafe_allow_html=True)

    with role_col:
        _render_role_selector(ctx.app_role)

    with bell_col:
        with st.popover(f"🔔 {unread}", use_container_width=True, key="header_notifications_popover"):
            render_notification_center(notifications_df)

    with profile_col:
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



def render_sidebar(ctx) -> None:
    page_icons = {
        "Dashboard": "📊",
        "Claims": "🗂️",
        "Claim Details": "📄",
        "Reports": "📈",
        "Admin": "⚙️",
    }

    with st.sidebar:
        st.markdown(
            """
            <div class="mm-sidebar-brand">
                <div class="mm-sidebar-brand-eyebrow">Insurance Operations</div>
                <div class="mm-sidebar-brand-title">MagMutual</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="mm-sidebar-divider"></div>', unsafe_allow_html=True)

        pages = allowed_pages(ctx.app_role)
        for page in pages:
            active = st.session_state.active_page == page
            icon = page_icons.get(page, "•")
            key_slug = page.lower().replace(" ", "_")
            key_prefix = "nav_active" if active else "nav"
            label = f"{icon}  {page}"

            if st.button(label, use_container_width=True, key=f"{key_prefix}_{key_slug}"):
                st.session_state.active_page = page
                st.rerun()

        if st.session_state.get("selected_claim_id"):
            st.caption(f"Selected claim: {st.session_state.selected_claim_id}")
