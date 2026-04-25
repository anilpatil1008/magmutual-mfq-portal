import streamlit as st
from pathlib import Path

from utils.constants import NAV_ITEMS, ROLES
from utils.helpers import set_page


def load_css() -> None:
    css_path = Path(__file__).resolve().parent.parent / "styles" / "carbon_like.css"

    if not css_path.exists():
        return

    try:
        with css_path.open("r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except OSError:
        # Safe fallback: continue rendering without custom CSS.
        return


def render_shell(username: str):
    st.markdown("<div class='app-shell'>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("<div class='brand'>MagMutual</div>", unsafe_allow_html=True)
        st.caption("MFQ Enterprise Portal")
        st.markdown("<div class='nav-header'>Navigation</div>", unsafe_allow_html=True)
        for item in NAV_ITEMS:
            if st.button(item, use_container_width=True, key=f"nav_{item}"):
                set_page(item)
                st.rerun()

    selected_role = st.session_state.active_role
    c1, c2, c3 = st.columns([5, 2, 2])
    with c1:
        st.markdown("<h1 class='header-title'>MagMutual MFQ Enterprise Portal</h1>", unsafe_allow_html=True)
    with c2:
        selected_role = st.selectbox(
            "Role",
            ROLES,
            key="active_role",
            label_visibility="collapsed",
            help="Role switcher",
        )
    with c3:
        notifications = st.session_state.get("notifications", 0)
        st.markdown(
            f"<div class='header-user-group'><span class='notif-bell'>🔔 {notifications}</span>"
            f"<span class='user-chip'>Snowflake • {username}</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='content-wrap'>", unsafe_allow_html=True)
    return selected_role


def close_shell():
    st.markdown("</div></div>", unsafe_allow_html=True)
