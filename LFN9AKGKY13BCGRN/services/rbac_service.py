from __future__ import annotations

from dataclasses import dataclass
import logging
import math

import streamlit as st

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UserContext:
    username: str
    sf_role: str
    display_name: str = "User"
    email: str = "N/A"


_EMPTY_CONTEXT_VALUES = {"", "none", "null", "nan", "n/a"}


def _clean_context_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    cleaned = str(value).strip()
    if cleaned.casefold() in _EMPTY_CONTEXT_VALUES:
        return ""
    return cleaned


def _get_streamlit_user_value(attribute_name: str) -> str:
    try:
        user = getattr(st, "user", None)
    except Exception as ex:  # pragma: no cover - runtime compatibility guard
        logger.debug("Unable to read st.user.%s: %s", attribute_name, ex)
        return ""

    if user is None:
        return ""

    value = ""
    try:
        value = getattr(user, attribute_name, "")
    except Exception as ex:  # pragma: no cover - runtime compatibility guard
        logger.debug("Unable to read st.user.%s attribute: %s", attribute_name, ex)

    if not value and hasattr(user, "get"):
        try:
            value = user.get(attribute_name, "")
        except Exception as ex:  # pragma: no cover - runtime compatibility guard
            logger.debug("Unable to read st.user[%s]: %s", attribute_name, ex)

    return _clean_context_value(value)


@st.cache_data(show_spinner=False, ttl=300)
def _get_current_user_cached(_session) -> str:
    try:
        row = _session.sql("SELECT CURRENT_USER() AS USER_NAME").to_pandas().iloc[0]
    except Exception as ex:  # pragma: no cover - safety path for local/non-Snowflake runtimes
        logger.warning("Unable to fetch CURRENT_USER(): %s", ex)
        return ""
    return _clean_context_value(row.get("USER_NAME"))


def get_current_user(session) -> str:
    streamlit_user_name = _get_streamlit_user_value("user_name")
    if streamlit_user_name:
        return streamlit_user_name
    return _get_current_user_cached(session)


def get_current_user_email() -> str:
    return _get_streamlit_user_value("email")


@st.cache_data(show_spinner=False, ttl=300)
def _get_current_role_cached(_session) -> str:
    try:
        row = _session.sql("SELECT CURRENT_ROLE() AS ROLE_NAME").to_pandas().iloc[0]
    except Exception as ex:  # pragma: no cover - safety path for local/non-Snowflake runtimes
        logger.warning("Unable to fetch CURRENT_ROLE(): %s", ex)
        return ""
    return _clean_context_value(row.get("ROLE_NAME"))


def get_current_role(session) -> str:
    return _get_current_role_cached(session)


@st.cache_data(show_spinner=False, ttl=300)
def get_available_roles_for_current_user(_session) -> list[str]:
    try:
        roles_df = _session.sql("""
            SELECT VALUE::STRING AS ROLE_NAME
            FROM TABLE(FLATTEN(INPUT => PARSE_JSON(CURRENT_AVAILABLE_ROLES())))
            ORDER BY ROLE_NAME
        """).to_pandas()
    except Exception as ex:
        logger.warning("Unable to fetch CURRENT_AVAILABLE_ROLES(); falling back to CURRENT_ROLE(): %s", ex)
        current_role = get_current_role(_session)
        return [current_role] if current_role else []

    if roles_df.empty or "ROLE_NAME" not in roles_df.columns:
        return []

    return sorted(
        {
            role_name
            for role_name in (_clean_context_value(role) for role in roles_df["ROLE_NAME"].tolist())
            if role_name
        }
    )


def get_available_roles(session) -> tuple[list[str], str]:
    current_role = get_current_role(session)
    available_roles = get_available_roles_for_current_user(_session=session)
    if not available_roles and current_role:
        available_roles = [current_role]
    return available_roles, current_role


def get_selected_sf_role(session) -> str:
    available_roles, current_role = get_available_roles(session)
    selected_role = _clean_context_value(st.session_state.get("selected_sf_role"))
    if selected_role and selected_role in available_roles:
        return selected_role
    if current_role and current_role in available_roles:
        return current_role
    if available_roles:
        return available_roles[0]
    return current_role or "Unknown"


def get_current_user_context(session) -> UserContext:
    username = get_current_user(session)
    email = get_current_user_email()
    sf_role = get_selected_sf_role(session)
    display_name = username or "User"
    profile = {
        "display_name": display_name,
        "full_name": display_name,
        "name": display_name,
        "username": username or "Unknown",
        "email": email or "N/A",
        "sf_role": sf_role or "Unknown",
    }
    st.session_state["user_profile"] = profile
    st.session_state["username"] = profile["username"]
    st.session_state["user_email"] = profile["email"]
    st.session_state["sf_role"] = profile["sf_role"]
    return UserContext(
        username=profile["username"],
        sf_role=profile["sf_role"],
        display_name=profile["display_name"],
        email=profile["email"],
    )


@st.cache_data(show_spinner=False, ttl=300)
def _get_session_context_snapshot_cached(_session, cache_scope: str) -> dict[str, str]:
    del cache_scope
    row = _session.sql("""
        SELECT
            CURRENT_USER() AS CURRENT_USER,
            CURRENT_ROLE() AS CURRENT_ROLE,
            CURRENT_WAREHOUSE() AS CURRENT_WAREHOUSE,
            CURRENT_DATABASE() AS CURRENT_DATABASE,
            CURRENT_SCHEMA() AS CURRENT_SCHEMA
    """).to_pandas().iloc[0]
    return {k: str(v or "").strip() for k, v in row.to_dict().items()}


def get_session_context_snapshot(session) -> dict[str, str]:
    cache_scope = str(st.session_state.get("selected_sf_role") or "default")
    return _get_session_context_snapshot_cached(session, cache_scope)


def _normalize_identifier(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip().upper()


def _normalize_status(value: object) -> str:
    return " ".join(str(value or "").replace("_", " ").split()).upper()


def can_edit_claim(claim_status: str, assigned_to: object, username: object) -> bool:
    """Return MFQ form editability from MFQ_STATUS, case/whitespace-insensitively."""
    normalized_status = _normalize_status(claim_status)
    is_assigned_user = _normalize_identifier(assigned_to) == _normalize_identifier(username)
    return normalized_status in {"MFQ GENERATED", "REJECTED"} or (
        normalized_status == "ASSIGNED" and is_assigned_user
    )
