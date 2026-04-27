from __future__ import annotations

import streamlit as st


def render_series_bar_chart(series, title: str) -> None:
    st.markdown(f"#### {title}")
    st.bar_chart(series)
