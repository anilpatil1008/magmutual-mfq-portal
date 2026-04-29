from __future__ import annotations

from collections.abc import Iterable

import streamlit as st

from services.snowflake_service import quote_sql, safe_collect_df


def validate_required_objects(session, requirements: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for req in requirements:
        object_name = req["object_name"]
        q = quote_sql(object_name.upper())
        df = safe_collect_df(
            session,
            f"""
            SELECT 1 AS FOUND FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = CURRENT_SCHEMA() AND TABLE_NAME = '{q}'
            UNION ALL
            SELECT 1 AS FOUND FROM INFORMATION_SCHEMA.VIEWS
            WHERE TABLE_SCHEMA = CURRENT_SCHEMA() AND TABLE_NAME = '{q}'
            LIMIT 1
            """,
        )
        if df.empty:
            missing.append(req)
    return missing


def render_missing_objects(missing: list[dict[str, str]]) -> None:
    if not missing:
        return
    st.error("Required Snowflake objects are missing. Please validate deployment objects before using dependent pages.")
    for item in missing:
        st.markdown(
            f"- Object: `{item['object_name']}` | Expected schema/database: `{item['expected_location']}` | Page dependency: `{item['page']}`"
        )
