from __future__ import annotations

import logging

import pandas as pd
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from config import snowflake_objects as obj
from repositories.dashboard_repository import get_dashboard_summary
from services.claim_service import get_claims_queue

logger = logging.getLogger(__name__)

DASHBOARD_METRIC_COLUMN_MAP = {
    "Total Active Claims": "TOTAL_ACTIVE_CLAIMS",
    "MFQ Generated": "MFQ_GENERATED_COUNT",
    "Assigned": "ASSIGNED_COUNT",
    "On Hold": "ON_HOLD_COUNT",
    "Approved": "APPROVED_COUNT",
    "Rejected": "REJECTED_COUNT",
}


def _empty_dashboard_metrics() -> dict[str, int]:
    return {metric: 0 for metric in DASHBOARD_METRIC_COLUMN_MAP}


def _show_dashboard_summary_error() -> None:
    message = f"Dashboard summary view not found or query failed: {obj.MFQ_DASHBOARD_SUMMARY_VIEW}"
    logger.error(message)
    st.error(message)


@st.cache_data(ttl=300, show_spinner=False)
def _get_dashboard_summary_cached(_session, cache_scope: str) -> pd.DataFrame:
    del cache_scope
    return get_dashboard_summary(_session)


def clear_dashboard_metrics_cache() -> None:
    """Invalidate dashboard summary metrics after claim status changes."""
    _get_dashboard_summary_cached.clear()


def get_dashboard_metrics(session, username: str) -> dict[str, int]:
    role_scope = str(st.session_state.get("selected_sf_role") or "default")
    cache_version = int(st.session_state.get("dashboard_metrics_cache_version", 0) or 0)
    cache_scope = f"{role_scope}:{id(session)}:{cache_version}"
    summary = (
        _get_dashboard_summary_cached(session, cache_scope)
        if get_script_run_ctx(suppress_warning=True) is not None
        else get_dashboard_summary(session)
    )
    if summary.empty:
        _show_dashboard_summary_error()
        return _empty_dashboard_metrics()

    row = summary.iloc[0]
    metrics: dict[str, int] = {}
    missing_columns: list[str] = []
    for metric_name, column_name in DASHBOARD_METRIC_COLUMN_MAP.items():
        if column_name not in summary.columns:
            missing_columns.append(column_name)
            metrics[metric_name] = 0
            continue
        metrics[metric_name] = int(row.get(column_name) or 0)

    if missing_columns:
        logger.error(
            "Dashboard summary view missing expected columns: %s; view=%s",
            ", ".join(missing_columns),
            obj.MFQ_DASHBOARD_SUMMARY_VIEW,
        )
        _show_dashboard_summary_error()
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
