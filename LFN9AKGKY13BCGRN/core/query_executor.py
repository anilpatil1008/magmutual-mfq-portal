from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)
SLOW_QUERY_THRESHOLD_MS = 1200


def execute_query(
    session,
    sql: str,
    *,
    params: dict[str, Any] | None = None,
    query_name: str = "query",
    as_dataframe: bool = True,
    fallback: pd.DataFrame | list[dict[str, Any]] | None = None,
) -> pd.DataFrame | list[dict[str, Any]]:
    """Execute a Snowflake query with consistent timing/error handling.

    Params are accepted for compatibility; callers should pass pre-escaped inputs
    until full Snowpark bind support is introduced across repositories.
    """
    start = time.perf_counter()
    try:
        if params:
            logger.debug("%s executed with params keys=%s", query_name, sorted(params.keys()))

        result = session.sql(sql).to_pandas()
        duration_ms = (time.perf_counter() - start) * 1000
        level = logging.WARNING if duration_ms >= SLOW_QUERY_THRESHOLD_MS else logging.INFO
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


def execute_query_df(session, sql: str, fallback: pd.DataFrame | None = None, query_name: str = "query") -> pd.DataFrame:
    """Backward-compatible dataframe wrapper for legacy repository calls."""
    result = execute_query(
        session,
        sql,
        query_name=query_name,
        as_dataframe=True,
        fallback=fallback if fallback is not None else pd.DataFrame(),
    )
    return result if isinstance(result, pd.DataFrame) else pd.DataFrame(result)
