import html
import streamlit as st


NAV_ITEMS = [
    ("Dashboard", "Dashboard", "⌂"),
    ("Claims", "Claims", "◫"),
    ("Reports", "Reports", "▤"),
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
                f"{page_icon}  {page_label}",
                use_container_width=True,
                key=f"nav_{page_key.lower()}",
                type="primary" if active_page == page_key else "secondary",
            )
            if clicked:
                _switch_page(page_key)

        if current_role == "ADMIN":
            clicked = st.button(
                "⚙  Admin",
                use_container_width=True,
                key="nav_admin",
                type="primary" if active_page == "Admin" else "secondary",
            )
            if clicked:
                _switch_page("Admin")


def render_topbar(display_name: str, email: str, role_options: list[str], current_role: str, notif_df) -> None:
    unread = 0
    if notif_df is not None and not notif_df.empty:
        unread = int((notif_df["IS_READ"] == False).sum())

    spacer, role_col, bell_col, user_col = st.columns([6.8, 2.3, 0.8, 2.3])

    with spacer:
        st.markdown('<div class="topbar-spacer"></div>', unsafe_allow_html=True)

    with role_col:
        selected_role = st.selectbox(
            "Role",
            role_options,
            index=role_options.index(current_role) if current_role in role_options else 0,
            label_visibility="collapsed",
            key="role_selector",
        )
        if selected_role != st.session_state.role_key:
            st.session_state.role_key = selected_role
            st.rerun()

    with bell_col:
        st.markdown(
            f"""
            <div class="notification-pill">
                <span class="notification-icon">🔔</span>
                <span class="notification-count">{unread}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with user_col:
        st.markdown(
            f"""
            <div class="profile-card">
                <div class="profile-avatar">{safe_str(initials(display_name))}</div>
                <div class="profile-details">
                    <div class="profile-name">{safe_str(display_name)}</div>
                    <div class="profile-email">{safe_str(email)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_page_title(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="page-title">{safe_str(title)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{safe_str(subtitle)}</div>', unsafe_allow_html=True)
