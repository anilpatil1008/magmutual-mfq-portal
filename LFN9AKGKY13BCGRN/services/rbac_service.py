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


def _get_first_row_value(row: object, *candidate_names: str) -> str:
    """Return a value from a pandas row using case-insensitive column matching."""
    if row is None:
        return ""

    row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
    normalized_candidates = {name.casefold() for name in candidate_names}
    for key, value in row_dict.items():
        if str(key).casefold() in normalized_candidates:
            return _clean_context_value(value)
    return ""


def _extract_column_values(df, *candidate_names: str) -> list[str]:
    """Return cleaned values from the first matching pandas column name."""
    normalized_candidates = {name.casefold() for name in candidate_names}
    for column in getattr(df, "columns", []):
        if str(column).casefold() in normalized_candidates:
            return [_clean_context_value(value) for value in df[column].tolist()]
    return []


def _dedupe_sorted(values: list[str]) -> list[str]:
    return sorted(
        {value for value in (_clean_context_value(item) for item in values) if value}
    )


def _quote_snowflake_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


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
    for user_container_name in ("user", "experimental_user"):
        try:
            user = getattr(st, user_container_name, None)
        except Exception as ex:  # pragma: no cover - runtime compatibility guard
            logger.debug(
                "Unable to read st.%s.%s: %s", user_container_name, attribute_name, ex
            )
            continue

        if user is None:
            continue

        value = ""
        try:
            value = getattr(user, attribute_name, "")
        except Exception as ex:  # pragma: no cover - runtime compatibility guard
            logger.debug(
                "Unable to read st.%s.%s attribute: %s",
                user_container_name,
                attribute_name,
                ex,
            )

        if not value and hasattr(user, "get"):
            try:
                value = user.get(attribute_name, "")
            except Exception as ex:  # pragma: no cover - runtime compatibility guard
                logger.debug(
                    "Unable to read st.%s[%s]: %s",
                    user_container_name,
                    attribute_name,
                    ex,
                )

        cleaned = _clean_context_value(value)
        if cleaned:
            return cleaned

    return ""


def _get_current_user_from_sql(_session) -> str:
    try:
        row = _session.sql("SELECT CURRENT_USER() AS USER_NAME").to_pandas().iloc[0]
    except Exception as ex:
        # pragma: no cover - safety path for local/non-Snowflake runtimes
        logger.warning("Unable to fetch CURRENT_USER(): %s", ex)
        return ""
    return _get_first_row_value(row, "USER_NAME", "CURRENT_USER")


def get_current_user(session) -> str:
    for attribute_name in ("user_name", "username", "login_name"):
        streamlit_user_name = _get_streamlit_user_value(attribute_name)
        if streamlit_user_name:
            return streamlit_user_name
    return _get_current_user_from_sql(session)


def get_current_user_email() -> str:
    return _get_streamlit_user_value("email")


def get_current_user_display_name(username: str) -> str:
    for attribute_name in ("name", "display_name", "full_name"):
        display_name = _get_streamlit_user_value(attribute_name)
        if display_name:
            return display_name
    return username


def _get_current_role_from_sql(_session) -> str:
    try:
        row = _session.sql("SELECT CURRENT_ROLE() AS ROLE_NAME").to_pandas().iloc[0]
    except Exception as ex:
        # pragma: no cover - safety path for local/non-Snowflake runtimes
        logger.warning("Unable to fetch CURRENT_ROLE(): %s", ex)
        return ""
    return _get_first_row_value(row, "ROLE_NAME", "CURRENT_ROLE")


def get_current_role(session) -> str:
    return _get_current_role_from_sql(session)


def _get_available_roles_from_current_available_roles(_session) -> list[str]:
    try:
        roles_df = _session.sql("""
            SELECT VALUE::STRING AS ROLE_NAME
            FROM TABLE(FLATTEN(INPUT => PARSE_JSON(CURRENT_AVAILABLE_ROLES())))
            ORDER BY ROLE_NAME
        """).to_pandas()
    except Exception as ex:
        logger.warning("Unable to fetch CURRENT_AVAILABLE_ROLES(): %s", ex)
        return []

    if roles_df.empty:
        return []

    return _dedupe_sorted(_extract_column_values(roles_df, "ROLE_NAME", "VALUE"))


def _get_available_roles_from_user_grants(_session, username: str) -> list[str]:
    if not username:
        return []

    quoted_username = _quote_snowflake_identifier(username)
    try:
        roles_df = _session.sql(f"SHOW GRANTS TO USER {quoted_username}").to_pandas()
    except Exception as ex:
        logger.warning("Unable to fetch SHOW GRANTS TO USER for %s: %s", username, ex)
        return []

    if roles_df.empty:
        return []

    granted_roles = []
    granted_to_values = _extract_column_values(roles_df, "granted_to", "GRANTED_TO")
    role_values = _extract_column_values(roles_df, "role", "ROLE")
    name_values = _extract_column_values(roles_df, "name", "NAME")

    if role_values:
        for index, role_name in enumerate(role_values):
            granted_to = (
                granted_to_values[index].casefold()
                if index < len(granted_to_values)
                else "role"
            )
            if not granted_to or granted_to == "role":
                granted_roles.append(role_name)
    elif name_values:
        for index, name in enumerate(name_values):
            granted_to = (
                granted_to_values[index].casefold()
                if index < len(granted_to_values)
                else "role"
            )
            if not granted_to or granted_to == "role":
                granted_roles.append(name)

    return _dedupe_sorted(granted_roles)


def get_available_roles_for_current_user(_session) -> list[str]:
    roles = _get_available_roles_from_current_available_roles(_session)
    if roles:
        return roles

    username = _get_current_user_from_sql(_session)
    roles = _get_available_roles_from_user_grants(_session, username)
    if roles:
        return roles

    current_role = get_current_role(_session)
    return [current_role] if current_role else []


def get_available_roles(session) -> tuple[list[str], str]:
    current_role = get_current_role(session)
    available_roles = get_available_roles_for_current_user(_session=session)
    if current_role:
        available_roles = _dedupe_sorted([*available_roles, current_role])
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
    display_name = get_current_user_display_name(username) or "User"
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
    is_assigned_user = _normalize_identifier(assigned_to) == _normalize_identifier(
        username
    )
    return normalized_status in {"MFQ GENERATED", "REJECTED"} or (
        normalized_status == "ASSIGNED" and is_assigned_user
    )
