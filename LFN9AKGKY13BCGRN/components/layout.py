from __future__ import annotations

import base64
from html import escape, unescape
from textwrap import dedent
from pathlib import Path
import re

import streamlit as st
from utils.streamlit_compat import safe_button, safe_child_columns, safe_child_container, safe_container, safe_popover, safe_rerun

from components.notifications import render_notification_center
from utils.navigation import (
    CLAIM_DETAILS_PAGE,
    CLAIM_DETAILS_VIEW,
    DASHBOARD_PAGE,
    DASHBOARD_VIEW,
    REPORTS_PAGE,
    REPORTS_VIEW,
    navigate_to_claim_details,
    navigate_to_dashboard,
    navigate_to_reports,
)

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


@st.cache_data(show_spinner=False)
def _load_app_css() -> str:
    css_file = Path(__file__).resolve().parent.parent / "styles" / "carbon_like.css"
    return css_file.read_text(encoding="utf-8") if css_file.exists() else ""


def load_css() -> None:
    app_css = _load_app_css()
    if app_css:
        st.markdown(f"<style>{app_css}</style>", unsafe_allow_html=True)
    st.markdown(_HIDE_DEFAULT_STREAMLIT_NAV_CSS, unsafe_allow_html=True)


def _render_role_selector(session, current_role: str) -> None:
    role_options = [str(role) for role in st.session_state.get("available_roles", []) if str(role).strip()]
    if not role_options:
        role_options = [current_role]
    elif current_role not in role_options:
        role_options = [current_role, *role_options]

    selected_role = st.selectbox(
        "Role",
        role_options,
        index=role_options.index(current_role),
        key="header_role_select",
        label_visibility="collapsed",
    )

    if selected_role != current_role:
        st.session_state["selected_sf_role"] = str(selected_role or "").strip()
        safe_rerun()


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


def _resolve_profile_display(ctx) -> tuple[str, str, str, str, str, str]:
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

    sf_role = _first_non_empty(
        st.session_state.get("selected_sf_role"),
        st.session_state.get("selected_role"),
        getattr(ctx, "sf_role", None),
        st.session_state.get("sf_role"),
    )

    initials = "".join(part[0] for part in short_name.split()[:2]).upper() or "U"
    return short_name, full_name, username, email_value, sf_role, initials



def render_header(session, ctx, notifications_df) -> None:
    unread = int((~notifications_df["IS_READ"]).sum()) if "IS_READ" in notifications_df.columns else 0

    short_name, full_name, username, email, sf_role, initials = _resolve_profile_display(ctx)
    safe_short_name = escape(short_name or "Profile")
    safe_full_name = escape(full_name or "N/A")
    safe_username = escape(username or "N/A")
    safe_email = escape(email or "N/A")
    safe_sf_role = escape(sf_role or "N/A")

    header_container = safe_container(key="app_topbar")
    actions_container = safe_child_container(header_container, key="portal_header_actions")
    role_col, bell_col, profile_col = safe_child_columns(actions_container, [380, 120, 330], gap="small")

    active_sf_role = st.session_state.get("selected_sf_role") or sf_role or ctx.sf_role
    with role_col:
        _render_role_selector(session, active_sf_role)

    with bell_col:
        with safe_popover(f"🔔 {unread}", use_container_width=True, key="header_notifications_popover"):
            render_notification_center(notifications_df)

    with profile_col:
        with safe_popover(
            f"{safe_short_name} ▾",
            use_container_width=True,
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
                                <div class="mm-profile-detail-row"><span class="mm-profile-detail-label">Snowflake Role</span><span class="mm-profile-detail-value">{safe_sf_role}</span></div>
                                <div class="mm-profile-detail-row"><span class="mm-profile-detail-label">Email</span><span class="mm-profile-detail-value">{safe_email}</span></div>
                            </div>
                        </div>
                    </div>
                    """
                ).strip(),
                unsafe_allow_html=True,
            )



def _sidebar_nav_items(current_view: str, selected_claim_id: str) -> list[tuple[str, str, object, bool]]:
    """Build sidebar items with ``current_view`` as the active-state source of truth."""
    normalized_view = str(current_view or DASHBOARD_VIEW).strip().lower()
    normalized_claim_id = str(selected_claim_id or "").strip()

    items: list[tuple[str, str, object, bool]] = [
        (DASHBOARD_PAGE, DASHBOARD_VIEW, navigate_to_dashboard, normalized_view == DASHBOARD_VIEW),
    ]

    if normalized_view == CLAIM_DETAILS_VIEW and normalized_claim_id:
        items.append(
            (
                CLAIM_DETAILS_PAGE,
                CLAIM_DETAILS_VIEW,
                lambda: navigate_to_claim_details(normalized_claim_id),
                True,
            )
        )

    items.append((REPORTS_PAGE, REPORTS_VIEW, navigate_to_reports, normalized_view == REPORTS_VIEW))
    return items


def render_sidebar(ctx) -> None:
    page_icons = {
        DASHBOARD_PAGE: ":material/dashboard:",
        CLAIM_DETAILS_PAGE: ":material/assignment:",
        REPORTS_PAGE: ":material/bar_chart:",
    }

    with st.sidebar:
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "magmutual_logo.png"
        logo_src = ""
        if logo_path.exists():
            logo_bytes = logo_path.read_bytes()
            logo_src = f"data:image/png;base64,{base64.b64encode(logo_bytes).decode('utf-8')}"

        st.markdown(
            f"""
            <div class="mm-sidebar-brand">
                <div class="mm-sidebar-brand-eyebrow">INSURANCE OPERATIONS</div>
                <div class="mm-sidebar-brand-row">
                    {f'<img class="brand-logo" src="{logo_src}" alt="MagMutual logo" />' if logo_src else ''}
                    <div class="mm-sidebar-brand-title">MagMutual</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="mm-sidebar-divider"></div>', unsafe_allow_html=True)

        current_view = str(st.session_state.get("current_view") or DASHBOARD_VIEW).strip().lower()
        selected_claim_id = str(st.session_state.get("selected_claim_id") or "").strip()
        for page, _view, navigate, active in _sidebar_nav_items(current_view, selected_claim_id):
            key_slug = page.lower().replace(" ", "_")
            key_prefix = "nav_active" if active else "nav"

            if safe_button(
                page,
                icon=page_icons.get(page, ":material/chevron_right:"),
                use_container_width=True,
                key=f"{key_prefix}_{key_slug}",
                type="secondary",
            ):
                st.query_params.clear()
                navigate()
