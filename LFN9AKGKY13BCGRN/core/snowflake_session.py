from __future__ import annotations

import os
from typing import Any

import streamlit as st
from snowflake.snowpark import Session

_SECRET_CANDIDATE_KEYS = ("snowflake", "connections", "snowflake_connection")
_CONFIG_KEYS = (
    "account",
    "user",
    "password",
    "authenticator",
    "role",
    "warehouse",
    "database",
    "schema",
)
_ENV_KEY_MAP = {
    "account": "SNOWFLAKE_ACCOUNT",
    "user": "SNOWFLAKE_USER",
    "password": "SNOWFLAKE_PASSWORD",
    "authenticator": "SNOWFLAKE_AUTHENTICATOR",
    "role": "SNOWFLAKE_ROLE",
    "warehouse": "SNOWFLAKE_WAREHOUSE",
    "database": "SNOWFLAKE_DATABASE",
    "schema": "SNOWFLAKE_SCHEMA",
}
_REQUIRED_EXTERNALBROWSER_KEYS = (
    "account",
    "user",
    "authenticator",
    "role",
    "warehouse",
    "database",
    "schema",
)
_REQUIRED_PASSWORD_KEYS = (
    "account",
    "user",
    "password",
    "role",
    "warehouse",
    "database",
    "schema",
)


def _get_active_session() -> Session | None:
    """Return Snowflake Streamlit's active session when running in Snowflake."""
    try:
        from snowflake.snowpark.context import get_active_session

        return get_active_session()
    except Exception:
        return None


def is_active_session_available() -> bool:
    """Return whether Snowflake's active Streamlit session is available."""
    return _get_active_session() is not None


def _read_streamlit_secrets() -> dict[str, Any]:
    """Read local-development Snowflake connection settings from st.secrets."""
    try:
        for key in _SECRET_CANDIDATE_KEYS:
            section = st.secrets.get(key)
            if section:
                return {k: section.get(k) for k in _CONFIG_KEYS if section.get(k) is not None}
        return {k: st.secrets.get(k) for k in _CONFIG_KEYS if st.secrets.get(k) is not None}
    except Exception:
        return {}


def _read_environment_variables() -> dict[str, Any]:
    """Read local-development Snowflake connection settings from environment variables."""
    return {k: os.getenv(env_key) for k, env_key in _ENV_KEY_MAP.items() if os.getenv(env_key)}


def _required_keys_for_authenticator(params: dict[str, Any]) -> tuple[str, ...]:
    authenticator = str(params.get("authenticator") or "").strip().lower()
    if authenticator == "externalbrowser":
        return _REQUIRED_EXTERNALBROWSER_KEYS
    return _REQUIRED_PASSWORD_KEYS


def _build_connection_parameters() -> dict[str, Any]:
    """Merge local secrets and environment variables for Snowflake Session.builder."""
    params = _read_streamlit_secrets()
    params.update(_read_environment_variables())

    params = {key: value for key, value in params.items() if value is not None and str(value).strip() != ""}
    required = _required_keys_for_authenticator(params)
    missing = [key for key in required if not params.get(key)]
    if missing:
        missing_str = ", ".join(missing)
        auth_hint = "externalbrowser" if str(params.get("authenticator") or "").strip().lower() == "externalbrowser" else "password"
        raise RuntimeError(
            f"Missing local Snowflake {auth_hint} connection settings: {missing_str}. "
            "Inside Snowflake Streamlit, the active session is used automatically. "
            "For local development, set the required values in .streamlit/secrets.toml "
            "or environment variables."
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
