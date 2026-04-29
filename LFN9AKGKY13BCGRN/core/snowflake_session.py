from __future__ import annotations

import streamlit as st
from snowflake.snowpark.context import get_active_session


@st.cache_resource(show_spinner=False)
def get_snowflake_session():
    """Return cached active Snowpark session in Streamlit runtime."""
    return get_active_session()
