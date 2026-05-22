from __future__ import annotations

from html import escape, unescape
from textwrap import dedent
from pathlib import Path
import re

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


def _to_title_name(raw_value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", str(raw_value or "")).strip()
    if not cleaned:
        return ""
    parts = [part.capitalize() for part in cleaned.split() if part]
    return " ".join(parts)


def _clean_profile_value(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    plain = re.sub(r"<[^>]+>", " ", unescape(raw))
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain


def _first_non_empty(*values: object) -> str:
    for value in values:
        candidate = _clean_profile_value(value)
        if candidate:
            return candidate
    return ""


def _resolve_profile_display(ctx) -> tuple[str, str, str, str, str, str, str]:
    username = _clean_profile_value(getattr(ctx, "username", ""))

    full_name_candidates = [
        getattr(ctx, "full_name", None),
        getattr(ctx, "name", None),
        st.session_state.get("full_name"),
        st.session_state.get("user_full_name"),
    ]
    user_profile = st.session_state.get("user_profile")
    if isinstance(user_profile, dict):
        full_name_candidates.extend([user_profile.get("full_name"), user_profile.get("name")])

    full_name = _first_non_empty(*full_name_candidates)

    if not full_name:
        full_name = _to_title_name(username) or "Unknown User"

    name_parts = [part for part in full_name.split() if part]
    short_name = " ".join(name_parts[:2]) if len(name_parts) >= 2 else full_name
    short_name = short_name.strip() or "Unknown User"

    email_candidates = [
        getattr(ctx, "email", None),
        st.session_state.get("user_email"),
        st.session_state.get("email"),
    ]
    if isinstance(user_profile, dict):
        email_candidates.append(user_profile.get("email"))

    email_value = _first_non_empty(*email_candidates)
    if "@" not in email_value:
        email_value = ""

    app_role = _first_non_empty(
        getattr(ctx, "app_role", None),
        st.session_state.get("app_role"),
    )
    sf_role = _first_non_empty(
        getattr(ctx, "sf_role", None),
        st.session_state.get("sf_role"),
    )

    initials = "".join(part[0] for part in short_name.split()[:2]).upper() or "U"
    return short_name, full_name, username, email_value, app_role, sf_role, initials



def render_header(ctx, notifications_df) -> None:
    unread = int((~notifications_df["IS_READ"]).sum()) if "IS_READ" in notifications_df.columns else 0

    short_name, full_name, username, email, app_role, sf_role, initials = _resolve_profile_display(ctx)
    safe_short_name = escape(short_name or "Profile")
    safe_full_name = escape(full_name or "N/A")
    safe_username = escape(username or "N/A")
    safe_email = escape(email or "N/A")
    safe_app_role = escape(app_role or "N/A")
    safe_sf_role = escape(sf_role or "N/A")

    header_container = st.container(key="app_topbar")
    spacer_col, role_col, bell_col, profile_col = header_container.columns([6, 2.2, 0.7, 1.0], gap="small")

    with spacer_col:
        st.empty()

    with role_col:
        _render_role_selector(ctx.app_role)

    with bell_col:
        with st.popover(f"🔔 {unread}", use_container_width=False, key="header_notifications_popover"):
            render_notification_center(notifications_df)

    with profile_col:
        with st.popover(
            f"{safe_short_name} ▾",
            use_container_width=False,
            key="header_profile_popover",
        ):
            st.markdown(
                dedent(
                    f"""
                    <div class="mm-profile-card">
                        <div class="mm-profile-card-head">
                            <span class="mm-avatar mm-avatar-lg">{escape(initials)}</span>
                            <div class="mm-profile-meta">
                                <div class="mm-profile-fullname">{safe_full_name}</div>
                                <div class="mm-profile-detail-row"><span class="mm-profile-detail-label">Name</span><span class="mm-profile-detail-value">{safe_full_name}</span></div>
                                <div class="mm-profile-detail-row"><span class="mm-profile-detail-label">Username</span><span class="mm-profile-detail-value">{safe_username}</span></div>
                                <div class="mm-profile-detail-row"><span class="mm-profile-detail-label">Role</span><span class="mm-profile-detail-value">{safe_app_role}</span></div>
                                <div class="mm-profile-detail-row"><span class="mm-profile-detail-label">Snowflake Role</span><span class="mm-profile-detail-value">{safe_sf_role}</span></div>
                                <div class="mm-profile-detail-row"><span class="mm-profile-detail-label">Email</span><span class="mm-profile-detail-value">{safe_email}</span></div>
                            </div>
                        </div>
                    </div>
                    """
                ).strip(),
                unsafe_allow_html=True,
            )



def render_sidebar(ctx) -> None:
    page_icons = {
        "Dashboard": ":material/dashboard:",
        "Claims": ":material/folder:",
        "Claim Details": ":material/description:",
        "Reports": ":material/bar_chart:",
        "Admin": ":material/settings:",
    }

    with st.sidebar:
        st.markdown(
            """
            <div class="mm-sidebar-brand">
                <div class="mm-sidebar-brand-eyebrow">INSURANCE OPERATIONS</div>
                <div class="mm-sidebar-brand-title">MagMutual</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="mm-sidebar-divider"></div>', unsafe_allow_html=True)

        pages = allowed_pages(ctx.app_role)
        for page in pages:
            active = st.session_state.active_page == page
            icon = page_icons.get(page, ":material/chevron_right:")
            key_slug = page.lower().replace(" ", "_")
            key_prefix = "nav_active" if active else "nav"

            if st.button(page, icon=icon, use_container_width=True, key=f"{key_prefix}_{key_slug}"):
                st.session_state.active_page = page
                st.rerun()

        if st.session_state.get("selected_claim_id"):
            st.caption(f"Selected claim: {st.session_state.selected_claim_id}")
