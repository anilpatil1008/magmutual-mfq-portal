import html
import streamlit as st


NAV_ITEMS = [
    ("Dashboard", "Dashboard", ":material/dashboard:"),
    ("Claims", "Claims", ":material/description:"),
    ("Reports", "Reports", ":material/bar_chart:"),
]


def safe_str(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def initials(name: str) -> str:
    parts = [p for p in str(name).split() if p.strip()]
    return "".join(p[0].upper() for p in parts[:2]) or "U"


def _switch_page(page_name: str) -> None:
    st.session_state.page = page_name
    st.session_state.selected_claim_id = None
    st.rerun()


def render_sidebar(current_role: str) -> None:
    active_page = st.session_state.get("page", "Dashboard")

    with st.sidebar:
        st.markdown(
            """
            <div class="brand-wrap">
                <span class="brand-drop"></span>
                <span>MagMutual</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("""<div class="nav-title">NAVIGATION</div>""", unsafe_allow_html=True)

        for page_key, page_label, page_icon in NAV_ITEMS:
            clicked = st.button(
                page_label,
                icon=page_icon,
                use_container_width=True,
                key=f"nav_{page_key.lower()}",
                type="primary" if active_page == page_key else "secondary",
            )
            if clicked:
                _switch_page(page_key)

        if current_role == "ADMIN":
            clicked = st.button(
                "Admin",
                icon=":material/settings:",
                use_container_width=True,
                key="nav_admin",
                type="primary" if active_page == "Admin" else "secondary",
            )
            if clicked:
                _switch_page("Admin")


def render_topbar(display_name: str, email: str, role_items: list[dict[str, str]], current_role: str, notif_df) -> None:
    unread = 0
    if notif_df is not None and not notif_df.empty and "IS_READ" in notif_df.columns:
        unread = int((notif_df["IS_READ"] == False).sum())

    current_label = next(
        (item["label"] for item in role_items if item["key"] == current_role),
        current_role.replace("_", " ").title(),
    )

    st.markdown('<div class="topbar-anchor"></div>', unsafe_allow_html=True)

    spacer, role_col, bell_col, user_col = st.columns(
        [8.2, 2.0, 0.55, 2.25],
        vertical_alignment="center",
    )

    with spacer:
        st.markdown('<div class="topbar-spacer"></div>', unsafe_allow_html=True)

    with role_col:
        with st.popover(f"🛡  {current_label}   ▾", use_container_width=True):
            st.markdown('<div class="role-switch-title">SWITCH ROLE</div>', unsafe_allow_html=True)
            for item in role_items:
                selected = item["key"] == current_role
                clicked = st.button(
                    item["label"],
                    icon=":material/check:" if selected else None,
                    key=f"switch_role_{item['key']}",
                    use_container_width=True,
                    type="secondary" if selected else "primary",
                )
                if clicked and item["key"] != current_role:
                    st.session_state.role_key = item["key"]
                    st.rerun()

    with bell_col:
        st.markdown(
            f"""
            <div class="topbar-bell-wrap">
                <div class="notification-pill">
                    <span class="notification-icon">🔔</span>
                    <span class="notification-badge">{unread}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with user_col:
        st.markdown(
            f"""
            <div class="topbar-profile-wrap">
                <div class="profile-card">
                    <div class="profile-avatar">{safe_str(initials(display_name))}</div>
                    <div class="profile-details">
                        <div class="profile-name">{safe_str(display_name)}</div>
                    </div>
                    <div class="profile-chevron">▾</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="fixed-topbar-offset"></div>', unsafe_allow_html=True)


def render_page_title(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="page-title">{safe_str(title)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{safe_str(subtitle)}</div>', unsafe_allow_html=True)
