from __future__ import annotations

import pandas as pd

from config import column_mappings as col
from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from repositories.claims_repository import object_exists


DASHBOARD_SUMMARY_COLUMNS = [
    col.TOTAL_ACTIVE_CLAIMS,
    col.MFQ_GENERATED_COUNT,
    col.ASSIGNED_COUNT,
    col.ON_HOLD_COUNT,
    col.APPROVED_COUNT,
    col.REJECTED_COUNT,
]


def get_dashboard_summary(session) -> pd.DataFrame:
    """Return the one-row dashboard KPI summary view, or an empty frame when unavailable."""
    if not object_exists(session, obj.MFQ_DASHBOARD_SUMMARY_VIEW):
        return pd.DataFrame(columns=DASHBOARD_SUMMARY_COLUMNS)

    return execute_query_df(
        session,
        f"""
        SELECT
          TOTAL_ACTIVE_CLAIMS,
          MFQ_GENERATED_COUNT,
          ASSIGNED_COUNT,
          ON_HOLD_COUNT,
          APPROVED_COUNT,
          REJECTED_COUNT
        FROM {obj.MFQ_DASHBOARD_SUMMARY_VIEW}
        LIMIT 1
        """,
        fallback=pd.DataFrame(columns=DASHBOARD_SUMMARY_COLUMNS),
        query_name="dashboard.get_dashboard_summary",
    )
