from __future__ import annotations

import time

import pandas as pd
import streamlit as st


def execute_query_df(session, sql: str, fallback: pd.DataFrame | None = None, query_name: str = "query") -> pd.DataFrame:
    start = time.perf_counter()
    try:
        result = session.sql(sql).to_pandas()
        duration_ms = (time.perf_counter() - start) * 1000
        st.caption(f"{query_name} executed in {duration_ms:.1f} ms")
        return result
    except Exception as exc:  # pragma: no cover
        duration_ms = (time.perf_counter() - start) * 1000
        msg = str(exc)
        if "does not exist" in msg.lower():
            st.error(f"Snowflake object missing for {query_name}: {msg}")
        elif "not authorized" in msg.lower() or "insufficient privileges" in msg.lower():
            st.error(f"Snowflake access denied for {query_name}: {msg}")
        else:
            st.error(f"Data query failed for {query_name} after {duration_ms:.1f} ms: {msg}")
        return fallback if fallback is not None else pd.DataFrame()
