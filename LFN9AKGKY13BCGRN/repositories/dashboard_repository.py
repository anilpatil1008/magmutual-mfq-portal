from __future__ import annotations

import logging

import pandas as pd

from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from repositories.claims_repository import object_exists

logger = logging.getLogger(__name__)

DASHBOARD_SUMMARY_COLUMNS = (
    "TOTAL_ACTIVE_CLAIMS",
    "MFQ_GENERATED_COUNT",
    "ASSIGNED_COUNT",
    "ON_HOLD_COUNT",
    "APPROVED_COUNT",
    "REJECTED_COUNT",
)


def get_dashboard_summary(session) -> pd.DataFrame:
    summary_view = obj.MFQ_DASHBOARD_SUMMARY_VIEW
    if not object_exists(session, summary_view):
        logger.error("Dashboard summary view not found: %s", summary_view)
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
        FROM {summary_view}
        """,
        query_name="dashboard.get_dashboard_summary",
    )
