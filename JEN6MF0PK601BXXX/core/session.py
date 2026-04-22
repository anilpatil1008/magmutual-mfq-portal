from __future__ import annotations

import streamlit as st


@st.cache_resource(show_spinner=False)
def get_session():
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except Exception:
        return None
