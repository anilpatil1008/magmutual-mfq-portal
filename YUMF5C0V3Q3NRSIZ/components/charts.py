from __future__ import annotations

import pandas as pd
import streamlit as st


def render_bar(df: pd.DataFrame, category_col: str, value_col: str = "COUNT", empty_label: str = "No data.") -> None:
    """Render a simple Streamlit bar chart from category/value columns."""
    if df.empty or category_col not in df.columns or value_col not in df.columns:
        st.caption(empty_label)
        return
    st.bar_chart(df.set_index(category_col)[value_col])
