from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st
from core.query_executor import execute_query_df
from core.snowflake_session import get_snowflake_session


def get_session():
    """Return cached Snowpark session in Snowflake Streamlit runtime."""
    return get_snowflake_session()


def safe_collect_df(session, sql: str, fallback: pd.DataFrame | None = None) -> pd.DataFrame:
    """Run SQL and return DataFrame; show UI error and fallback on failure."""
    try:
        return execute_query_df(session, sql, fallback=fallback, query_name="safe_collect_df")
    except Exception as exc:  # pragma: no cover - safety path for runtime env differences
        st.error(f"Data query failed: {exc}")
        return fallback if fallback is not None else pd.DataFrame()


def quote_sql(value: Any) -> str:
    """Lightweight single-quote escaping for dynamic SQL filters."""
    return str(value).replace("'", "''")
