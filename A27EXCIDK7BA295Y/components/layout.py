from __future__ import annotations

from html import escape
from pathlib import Path
import json
import re

import streamlit as st
from streamlit.components.v1 import html as components_html

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


def _resolve_profile_display(ctx) -> tuple[str, str, str, str | None, str]:
    username = str(getattr(ctx, "username", "") or "").strip()

    full_name_candidates = [
        getattr(ctx, "full_name", None),
        getattr(ctx, "name", None),
        st.session_state.get("full_name"),
        st.session_state.get("user_full_name"),
    ]
    user_profile = st.session_state.get("user_profile")
    if isinstance(user_profile, dict):
        full_name_candidates.extend([user_profile.get("full_name"), user_profile.get("name")])

    full_name = ""
    for candidate in full_name_candidates:
        value = str(candidate or "").strip()
        if value:
            full_name = value
            break

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

    email_value = None
    for candidate in email_candidates:
        value = str(candidate or "").strip()
        if value and "@" in value:
            email_value = value
            break

    initials = "".join(part[0] for part in short_name.split()[:2]).upper() or "U"
    return short_name, full_name, username, email_value, initials


def _attach_profile_hover_tooltip(tooltip_text: str) -> None:
    escaped_tooltip = json.dumps(tooltip_text)
    components_html(
        f"""
        <script>
        const tooltipText = {escaped_tooltip};
        function setProfileTooltip() {{
          const wrapper = window.parent.document.querySelector('.st-key-header_profile_popover');
          const btn = wrapper?.querySelector('[data-testid="stPopoverButton"]');
          if (wrapper) {{
            wrapper.setAttribute('data-profile-tooltip', tooltipText);
          }}
          if (btn) {{
            btn.setAttribute('title', tooltipText);
            btn.setAttribute('aria-label', tooltipText);
          }}
        }}
        setProfileTooltip();
        new MutationObserver(setProfileTooltip).observe(window.parent.document.body, {{childList: true, subtree: true}});
        </script>
        """,
        height=0,
        width=0,
    )


def render_header(ctx, notifications_df) -> None:
    unread = int((~notifications_df["IS_READ"]).sum()) if "IS_READ" in notifications_df.columns else 0

    short_name, full_name, username, email, initials = _resolve_profile_display(ctx)
    safe_full_name = escape(full_name)
    safe_username = escape(username)
    safe_email = escape(email) if email else ""
    safe_app_role = escape(str(getattr(ctx, "app_role", "") or ""))
    safe_sf_role = escape(str(getattr(ctx, "sf_role", "") or ""))

    header_container = st.container(key="app_topbar")
    left_col, right_col = header_container.columns([1.7, 1.3], gap="small")

    with left_col:
        st.markdown(
            """
            <div class="mm-topbar-title-wrap portal-header-left">
                <div class="mm-topbar-eyebrow">MagMutual Portal</div>
                <div class="mm-topbar-title">Medical Faculty Questionnaire</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        actions_container = st.container(key="portal_header_actions")
        role_col, bell_col, profile_col = actions_container.columns([2.2, 1.0, 2.8], gap="small")

        with role_col:
            _render_role_selector(ctx.app_role)

        with bell_col:
            with st.popover(f"🔔 {unread}", use_container_width=True, key="header_notifications_popover"):
                render_notification_center(notifications_df)

        with profile_col:
            tooltip_lines = [
                f"Name: {full_name}",
                f"Username: {username}",
            ]
            if email:
                tooltip_lines.append(f"Email: {email}")
            if getattr(ctx, "app_role", None):
                tooltip_lines.append(f"Role: {str(ctx.app_role)}")
            tooltip_text = "\n".join(tooltip_lines)

            with st.popover(
                f"{short_name} ▾",
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
                                <div class="mm-profile-username">Username: {safe_username}</div>
                                {"<div class='mm-profile-email'>Email: " + safe_email + "</div>" if safe_email else ""}
                                <div class="mm-profile-role">Role: {safe_app_role}{(" • " + safe_sf_role) if safe_sf_role else ""}</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            _attach_profile_hover_tooltip(tooltip_text)



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
