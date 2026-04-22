from __future__ import annotations

import streamlit as st


def render_admin() -> None:
    st.markdown("""<div class="page-title">Admin</div>""", unsafe_allow_html=True)
    st.markdown(
        """<div class="page-subtitle">User management, role mapping, and audit controls.</div>""",
        unsafe_allow_html=True,
    )
