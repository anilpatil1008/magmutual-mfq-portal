from __future__ import annotations

import os
from typing import Any

import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session

_SECRET_CANDIDATE_KEYS = ("snowflake", "connections", "snowflake_connection")
_CONFIG_KEYS = (
    "account",
    "user",
    "password",
    "role",
    "warehouse",
    "database",
    "schema",
)
_ENV_KEY_MAP = {
    "account": "SNOWFLAKE_ACCOUNT",
    "user": "SNOWFLAKE_USER",
    "password": "SNOWFLAKE_PASSWORD",
    "role": "SNOWFLAKE_ROLE",
    "warehouse": "SNOWFLAKE_WAREHOUSE",
    "database": "SNOWFLAKE_DATABASE",
    "schema": "SNOWFLAKE_SCHEMA",
}


def _get_active_session() -> Session | None:
    """Return Snowflake Streamlit's active session when running in Snowflake."""
    try:
        return get_active_session()
    except Exception:
        return None


def _read_streamlit_secrets() -> dict[str, Any]:
    """Read Snowflake connection settings from st.secrets if provided."""
    try:
        for key in _SECRET_CANDIDATE_KEYS:
            section = st.secrets.get(key)
            if section:
                return {k: section.get(k) for k in _CONFIG_KEYS if section.get(k)}
        return {k: st.secrets.get(k) for k in _CONFIG_KEYS if st.secrets.get(k)}
    except Exception:
        return {}


def _read_environment_variables() -> dict[str, Any]:
    """Read Snowflake connection settings from environment variables."""
    return {k: os.getenv(env_key) for k, env_key in _ENV_KEY_MAP.items() if os.getenv(env_key)}


def _build_connection_parameters() -> dict[str, Any]:
    """Merge secrets and environment variables for Snowflake Session.builder."""
    params = _read_streamlit_secrets()
    params.update(_read_environment_variables())

    required = ("account", "user", "password")
    missing = [k for k in required if not params.get(k)]
    if missing:
        missing_str = ", ".join(missing)
        raise RuntimeError(
            f"Missing Snowflake connection settings: {missing_str}. "
            "Set them in .streamlit/secrets.toml or environment variables."
        )

    return params


@st.cache_resource(show_spinner=False)
def get_snowflake_session() -> Session:
    """Return the active Snowflake session or create one from local settings."""
    active_session = _get_active_session()
    if active_session is not None:
        return active_session

    connection_parameters = _build_connection_parameters()
    return Session.builder.configs(connection_parameters).create()


def test_snowflake_connection() -> str:
    """Run a simple Snowflake connectivity query and return server timestamp."""
    session = get_snowflake_session()
    row = session.sql("SELECT CURRENT_TIMESTAMP() AS CURRENT_TS").collect()[0]
    return str(row["CURRENT_TS"])
