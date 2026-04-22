import html
import streamlit as st


def safe_str(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def initials(name: str) -> str:
    parts = [p for p in str(name).split() if p.strip()]
    return "".join(p[0].upper() for p in parts[:2]) or "U"


def render_sidebar(current_role: str) -> None:
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

        if st.button("Dashboard", use_container_width=True, key="nav_dashboard"):
            st.session_state.page = "Dashboard"
            st.session_state.selected_claim_id = None
            st.rerun()

        if st.button("Claims", use_container_width=True, key="nav_claims"):
            st.session_state.page = "Claims"
            st.session_state.selected_claim_id = None
            st.rerun()

        if st.button("Reports", use_container_width=True, key="nav_reports"):
            st.session_state.page = "Reports"
            st.session_state.selected_claim_id = None
            st.rerun()

        if current_role == "ADMIN":
            if st.button("Admin", use_container_width=True, key="nav_admin"):
                st.session_state.page = "Admin"
                st.session_state.selected_claim_id = None
                st.rerun()


def render_topbar(display_name: str, email: str, role_options: list[str], current_role: str, notif_df) -> None:
    unread = 0
    if notif_df is not None and not notif_df.empty:
        unread = len(notif_df[notif_df["IS_READ"] == False])

    left, role_col, bell_col, user_col = st.columns([6.5, 2.2, 0.9, 2.4])

    with role_col:
        st.markdown('<div class="topbar-box">', unsafe_allow_html=True)
        selected_role = st.selectbox(
            "Role",
            role_options,
            index=role_options.index(current_role) if current_role in role_options else 0,
            label_visibility="collapsed",
            key="role_selector",
        )
        st.markdown("</div>", unsafe_allow_html=True)
        if selected_role != st.session_state.role_key:
            st.session_state.role_key = selected_role
            st.rerun()

    with bell_col:
        st.markdown(
            f"""
            <div class="topbar-box topbar-bell">
                <span class="bell-icon">🔔</span>
                <span class="bell-count">{unread}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with user_col:
        st.markdown(
            f"""
            <div class="topbar-box">
                <div class="user-inline">
                    <span class="user-badge">{safe_str(initials(display_name))}</span>
                    <div class="user-text-wrap">
                        <div class="topbar-user-name">{safe_str(display_name)}</div>
                        <div class="topbar-user-email">{safe_str(email)}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_page_title(title: str, subtitle: str) -> None:
    st.markdown(f"""<div class="page-title">{safe_str(title)}</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="page-subtitle">{safe_str(subtitle)}</div>""", unsafe_allow_html=True)