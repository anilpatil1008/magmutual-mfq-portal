from __future__ import annotations

import logging
import os
import time
from collections.abc import Sequence
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)
SLOW_QUERY_THRESHOLD_MS = 1200


def app_debug_enabled() -> bool:
    return str(os.getenv("APP_DEBUG", "")).strip().lower() in {"1", "true", "yes", "on"}


def execute_query(
    session,
    sql: str,
    *,
    params: Sequence[Any] | dict[str, Any] | None = None,
    query_name: str = "query",
    as_dataframe: bool = True,
    fallback: pd.DataFrame | list[dict[str, Any]] | None = None,
) -> pd.DataFrame | list[dict[str, Any]]:
    """Execute a Snowflake query with consistent timing/error handling.

    Params are forwarded to Snowpark so callers can bind user-provided values
    instead of interpolating them into SQL strings.
    """
    start = time.perf_counter()
    try:
        if params:
            if isinstance(params, dict):
                logger.debug("%s executed with params keys=%s", query_name, sorted(params.keys()))
            else:
                logger.debug("%s executed with %d bind params", query_name, len(params))

        statement = session.sql(sql, params=params) if params else session.sql(sql)
        result = statement.to_pandas()
        duration_ms = (time.perf_counter() - start) * 1000
        if app_debug_enabled() or duration_ms >= SLOW_QUERY_THRESHOLD_MS:
            level = logging.DEBUG if app_debug_enabled() else logging.WARNING
            logger.log(level, "query=%s duration_ms=%.1f rows=%s", query_name, duration_ms, len(result))

        if as_dataframe:
            return result
        return result.to_dict(orient="records") if not result.empty else []
    except Exception as exc:  # pragma: no cover
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception("query_failed=%s duration_ms=%.1f", query_name, duration_ms)
        if fallback is not None:
            return fallback
        return pd.DataFrame() if as_dataframe else []


def execute_query_df(
    session,
    sql: str,
    fallback: pd.DataFrame | None = None,
    query_name: str = "query",
    params: Sequence[Any] | dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Backward-compatible dataframe wrapper for legacy repository calls."""
    result = execute_query(
        session,
        sql,
        params=params,
        query_name=query_name,
        as_dataframe=True,
        fallback=fallback if fallback is not None else pd.DataFrame(),
    )
    return result if isinstance(result, pd.DataFrame) else pd.DataFrame(result)
