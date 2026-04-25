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


def render_shell():
    st.markdown("<div class='app-shell'>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class='top-header'>
            <div class='header-title'>MagMutual MFQ Enterprise Portal</div>
            <div class='header-right'>
                <div class='notif'>🔔</div>
                <div class='user-chip'>Signed in via Snowflake</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("<div class='brand'>MagMutual</div>", unsafe_allow_html=True)
        selected_role = st.selectbox("Role", ROLES, key="active_role")
        for item in NAV_ITEMS:
            if st.button(item, use_container_width=True, key=f"nav_{item}"):
                set_page(item)
                st.rerun()

    st.markdown("<div class='content-wrap'>", unsafe_allow_html=True)
    return selected_role


def close_shell():
    st.markdown("</div></div>", unsafe_allow_html=True)
