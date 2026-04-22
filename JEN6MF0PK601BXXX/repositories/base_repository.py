from __future__ import annotations

import pandas as pd

from core.session import get_session


def run_query(sql: str) -> pd.DataFrame:
    session = get_session()
    if session is None:
        raise RuntimeError("No active Snowflake session found. Run inside Streamlit in Snowflake.")
    return session.sql(sql).to_pandas()


def exec_sql(sql: str) -> None:
    session = get_session()
    if session is None:
        raise RuntimeError("No active Snowflake session found. Run inside Streamlit in Snowflake.")
    session.sql(sql).collect()


def esc(value: str) -> str:
    return str(value).replace("'", "''")
