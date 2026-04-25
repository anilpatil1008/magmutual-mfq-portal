from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st
from snowflake.snowpark.context import get_active_session


def get_session():
    """Return active Snowpark session in Snowflake Streamlit runtime."""
    return get_active_session()


def safe_collect_df(session, sql: str, fallback: pd.DataFrame | None = None) -> pd.DataFrame:
    """Run SQL and return DataFrame; show UI error and fallback on failure."""
    try:
        return session.sql(sql).to_pandas()
    except Exception as exc:  # pragma: no cover - safety path for runtime env differences
        st.error(f"Data query failed: {exc}")
        return fallback if fallback is not None else pd.DataFrame()


def quote_sql(value: Any) -> str:
    """Lightweight single-quote escaping for dynamic SQL filters."""
    return str(value).replace("'", "''")
