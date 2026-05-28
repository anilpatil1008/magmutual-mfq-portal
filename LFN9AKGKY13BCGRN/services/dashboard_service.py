from __future__ import annotations

import logging

import pandas as pd

from config import column_mappings as col
from repositories import dashboard_repository
from services.claim_service import get_claims_queue

logger = logging.getLogger(__name__)

_DASHBOARD_METRIC_DEFAULTS = {
    "Total Active Claims": 0,
    "MFQ Generated": 0,
    "Assigned": 0,
    "On Hold": 0,
    "Approved": 0,
    "Rejected": 0,
}

_DASHBOARD_SUMMARY_TO_METRIC_LABEL = {
    col.TOTAL_ACTIVE_CLAIMS: "Total Active Claims",
    col.MFQ_GENERATED_COUNT: "MFQ Generated",
    col.ASSIGNED_COUNT: "Assigned",
    col.ON_HOLD_COUNT: "On Hold",
    col.APPROVED_COUNT: "Approved",
    col.REJECTED_COUNT: "Rejected",
}


def _safe_int(value) -> int:
    if pd.isna(value):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.warning("dashboard_summary_non_numeric_value=%r", value)
        return 0


def get_dashboard_metrics(session, username: str) -> dict[str, int]:
    """Return dashboard KPI card counts from the Snowflake summary view."""
    # Username is kept for API compatibility with existing dashboard callers.
    _ = username
    summary = dashboard_repository.get_dashboard_summary(session)
    if summary.empty:
        logger.warning("dashboard_summary_view_empty_or_missing")
        return _DASHBOARD_METRIC_DEFAULTS.copy()

    row = summary.iloc[0]
    metrics = _DASHBOARD_METRIC_DEFAULTS.copy()
    for source_column, metric_label in _DASHBOARD_SUMMARY_TO_METRIC_LABEL.items():
        if source_column not in summary.columns:
            logger.warning("dashboard_summary_missing_column=%s", source_column)
            continue
        metrics[metric_label] = _safe_int(row[source_column])
    return metrics


def get_dashboard_charts(session, username: str) -> dict[str, pd.DataFrame]:
    claims = get_claims_queue(session, username=username)
    if claims.empty:
        return {
            "status": pd.DataFrame(columns=["STATUS", "COUNT"]),
            "specialty": pd.DataFrame(columns=["SPECIALTY", "COUNT"]),
            "priority": pd.DataFrame(columns=["PRIORITY", "COUNT"]),
        }

    return {
        "status": claims.groupby("STATUS").size().reset_index(name="COUNT"),
        "specialty": claims.groupby("SPECIALTY").size().reset_index(name="COUNT"),
        "priority": claims.groupby("PRIORITY").size().reset_index(name="COUNT"),
    }
