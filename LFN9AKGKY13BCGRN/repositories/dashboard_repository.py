from __future__ import annotations

import pandas as pd

from config import snowflake_objects as obj
from core.query_executor import execute_query_df


def get_dashboard_kpis(session) -> pd.DataFrame:
    return execute_query_df(
        session,
        f"""
        SELECT
            COUNT(*) AS TOTAL_ACTIVE_CLAIMS,
            COUNT_IF(STATUS = 'MFQ Generated') AS MFQ_GENERATED,
            COUNT_IF(STATUS = 'Assigned') AS ASSIGNED,
            COUNT_IF(STATUS = 'On Hold') AS ON_HOLD,
            COUNT_IF(STATUS = 'Approved') AS APPROVED,
            COUNT_IF(STATUS = 'Rejected') AS REJECTED
        FROM {obj.MFQ_RECENT_CLAIMS_VIEW}
        """,
        query_name="dashboard.get_dashboard_kpis",
    )
