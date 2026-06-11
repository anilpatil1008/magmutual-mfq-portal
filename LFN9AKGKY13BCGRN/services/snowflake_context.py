from __future__ import annotations

import logging
import math
import os
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)

_EMPTY_CONTEXT_VALUES = {"", "none", "null", "nan", "n/a"}
_DEFAULT_APP_ROLE = "FR_MFQ_APPDEV"
_SELECTED_APP_ROLE_KEY = "selected_app_role"
_LEGACY_SELECTED_ROLE_KEY = "selected_sf_role"


def _is_role_debug_enabled() -> bool:
    return os.getenv("APP_DEBUG", "false").lower() in ("1", "true", "yes", "y")


def _debug_log(message: str, *args: object) -> None:
    if _is_role_debug_enabled():
        logger.debug(message, *args)


def _clean_context_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    cleaned = str(value).strip()
    if cleaned.casefold() in _EMPTY_CONTEXT_VALUES:
        return ""
    return cleaned


def _dedupe_sorted(values: list[str]) -> list[str]:
    return sorted(
        {value for value in (_clean_context_value(item) for item in values) if value}
    )


def _extract_column_values(df: Any, *candidate_names: str) -> list[str]:
    normalized_candidates = {name.casefold() for name in candidate_names}
    for column in getattr(df, "columns", []):
        if str(column).casefold() in normalized_candidates:
            return [_clean_context_value(value) for value in df[column].tolist()]
    return []


def _get_first_row_value(row: object, *candidate_names: str) -> str:
    if row is None:
        return ""

    row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
    normalized_candidates = {name.casefold() for name in candidate_names}
    for key, value in row_dict.items():
        if str(key).casefold() in normalized_candidates:
            return _clean_context_value(value)
    return ""


def quote_snowflake_identifier(identifier: str) -> str:
    """Return a safely double-quoted Snowflake identifier."""
    return '"' + str(identifier or "").replace('"', '""') + '"'


def _get_streamlit_user_value(attribute_name: str) -> str:
    """Read viewer metadata from Streamlit identity, preferring st.user."""
    for user_container_name in ("user", "experimental_user"):
        try:
            user = getattr(st, user_container_name, None)
        except Exception as ex:  # pragma: no cover - runtime compatibility guard
            _debug_log(
                "Unable to read st.%s.%s: %s", user_container_name, attribute_name, ex
            )
            continue

        if user is None:
            continue

        value = ""
        try:
            value = getattr(user, attribute_name, "")
        except Exception as ex:  # pragma: no cover - runtime compatibility guard
            _debug_log(
                "Unable to read st.%s.%s attribute: %s",
                user_container_name,
                attribute_name,
                ex,
            )

        if not value and hasattr(user, "get"):
            try:
                value = user.get(attribute_name, "")
            except Exception as ex:  # pragma: no cover - runtime compatibility guard
                _debug_log(
                    "Unable to read st.%s[%s]: %s",
                    user_container_name,
                    attribute_name,
                    ex,
                )

        cleaned = _clean_context_value(value)
        if cleaned:
            return cleaned

    return ""


def _get_current_user_from_sql(session) -> str:
    try:
        row = session.sql("SELECT CURRENT_USER() AS USER_NAME").to_pandas().iloc[0]
    except Exception as ex:
        _debug_log("Unable to fetch CURRENT_USER(): %s", ex)
        return ""
    return _get_first_row_value(row, "USER_NAME", "CURRENT_USER")


def get_viewer_user(session=None) -> dict[str, str]:
    """Return the actual Streamlit viewer identity, never relying only on SQL.

    In Snowflake Streamlit warehouse runtime, CURRENT_USER() is owner/session
    context. st.user.user_name and st.user.email are therefore the authoritative
    viewer identity fields when present.
    """
    username = ""
    for attribute_name in ("user_name", "username", "login_name"):
        username = _get_streamlit_user_value(attribute_name)
        if username:
            break

    if not username and session is not None:
        username = _get_current_user_from_sql(session)

    display_name = ""
    for attribute_name in ("name", "display_name", "full_name"):
        display_name = _get_streamlit_user_value(attribute_name)
        if display_name:
            break

    username = username or "Unknown"
    return {
        "username": username,
        "user_name": username,
        "display_name": display_name or username or "User",
        "email": _get_streamlit_user_value("email") or "N/A",
    }


def get_current_owner_role(session) -> str:
    """Return CURRENT_ROLE(), which is the runtime owner/session role."""
    try:
        row = session.sql("SELECT CURRENT_ROLE() AS ROLE_NAME").to_pandas().iloc[0]
    except Exception as ex:
        _debug_log("Unable to fetch CURRENT_ROLE(): %s", ex)
        return ""
    return _get_first_row_value(row, "ROLE_NAME", "CURRENT_ROLE")


def _set_role_debug_context(**updates: object) -> None:
    debug_context = dict(st.session_state.get("role_debug_context") or {})
    debug_context.update(updates)
    st.session_state["role_debug_context"] = debug_context


def _read_show_grants_roles(session) -> list[str]:
    rows = session.sql("""
        SELECT "name" AS ROLE_NAME
        FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
        WHERE UPPER("granted_on") = 'ROLE'
        ORDER BY ROLE_NAME
    """).collect()

    roles: list[str] = []
    for row in rows:
        try:
            role_name = row["ROLE_NAME"]
        except Exception:
            try:
                role_name = getattr(row, "ROLE_NAME")
            except Exception:
                role_name = row[0] if row else ""
        cleaned_role = _clean_context_value(role_name)
        if cleaned_role and cleaned_role.upper().startswith("FR_MFQ_"):
            roles.append(cleaned_role.upper())
    return _dedupe_sorted(roles)


def _get_roles_from_show_grants(session, viewer_username: str) -> list[str]:
    cleaned_username = _clean_context_value(viewer_username)
    if not cleaned_username or cleaned_username == "Unknown":
        return []

    safe_user = quote_snowflake_identifier(cleaned_username.upper())
    try:
        session.sql(f"SHOW GRANTS TO USER {safe_user}").collect()
        roles = _read_show_grants_roles(session)
        _set_role_debug_context(show_grants_error="", show_grants_roles=roles)
        return roles
    except Exception as ex:
        warning = (
            f"Unable to dynamically fetch user roles: {ex}. "
            "Ask the Snowflake admin/lead to allow the app owner role to view user grants "
            "or approve another secure approach."
        )
        _debug_log("Unable to fetch SHOW GRANTS roles for %s: %s", cleaned_username, ex)
        _set_role_debug_context(show_grants_error=warning, show_grants_roles=[])
        try:
            st.warning(warning)
        except Exception:  # pragma: no cover - non-Streamlit test/runtime guard
            pass
        return []


def get_viewer_granted_roles(session) -> list[str]:
    """Return FR_MFQ roles granted to the Streamlit viewer, with safe fallbacks."""
    viewer = get_viewer_user(session)
    viewer_username = _clean_context_value(viewer.get("user_name"))
    st_user_name = _get_streamlit_user_value("user_name")

    viewer_roles = _get_roles_from_show_grants(session, viewer_username)
    if viewer_roles:
        roles = viewer_roles
    else:
        owner_role = get_current_owner_role(session)
        roles = [owner_role] if owner_role else ["Unknown"]

    roles = _dedupe_sorted(roles)
    _set_role_debug_context(
        st_user_name=st_user_name,
        viewer_user=viewer_username,
        final_dropdown_roles=roles,
    )
    return roles


def get_role_dropdown_options(session) -> list[str]:
    """Return the app-level role dropdown options for UI/profile logic only."""
    return get_viewer_granted_roles(session)


def set_selected_app_role(role_name: object) -> str:
    """Store the app-level selected role without switching SQL execution role."""
    selected_role = _clean_context_value(role_name) or "Unknown"
    st.session_state[_SELECTED_APP_ROLE_KEY] = selected_role
    st.session_state["selected_role"] = selected_role
    # Keep the legacy key synchronized so existing cache scopes and page state
    # continue to behave exactly as before while the canonical key moves to
    # selected_app_role.
    st.session_state[_LEGACY_SELECTED_ROLE_KEY] = selected_role
    st.session_state["sf_role"] = selected_role
    return selected_role


def get_selected_app_role(session) -> str:
    """Resolve and persist the selected app-level role for UI decisions."""
    role_options = get_role_dropdown_options(session)
    owner_role = get_current_owner_role(session)

    selected_role = _clean_context_value(st.session_state.get(_SELECTED_APP_ROLE_KEY))
    if selected_role and selected_role in role_options:
        return set_selected_app_role(selected_role)

    dropdown_role = _clean_context_value(st.session_state.get("selected_role"))
    if dropdown_role and dropdown_role in role_options:
        return set_selected_app_role(dropdown_role)

    legacy_role = _clean_context_value(st.session_state.get(_LEGACY_SELECTED_ROLE_KEY))
    if legacy_role and legacy_role in role_options:
        return set_selected_app_role(legacy_role)

    if _DEFAULT_APP_ROLE in role_options:
        return set_selected_app_role(_DEFAULT_APP_ROLE)

    if role_options:
        fallback_role = role_options[0]
        if fallback_role:
            return set_selected_app_role(fallback_role)

    if owner_role:
        return set_selected_app_role(owner_role)

    return set_selected_app_role("Unknown")




def _safe_scalar_sql(session, query: str, column_name: str) -> str:
    try:
        row = session.sql(query).to_pandas().iloc[0]
    except Exception as ex:
        return f"Unavailable: {ex}"
    return _get_first_row_value(row, column_name) or "Unavailable"


def render_role_debug_expander(session) -> None:
    """Render temporary Snowflake-only role diagnostics for deployed debugging."""
    try:
        from core.snowflake_session import is_active_session_available

        if not is_active_session_available():
            return
    except Exception:
        return

    debug_context = dict(st.session_state.get("role_debug_context") or {})
    debug_context["current_user"] = _safe_scalar_sql(
        session, "SELECT CURRENT_USER() AS CURRENT_USER", "CURRENT_USER"
    )
    debug_context["current_role"] = _safe_scalar_sql(
        session, "SELECT CURRENT_ROLE() AS CURRENT_ROLE", "CURRENT_ROLE"
    )
    debug_context["selected_role"] = _clean_context_value(
        st.session_state.get("selected_role")
        or st.session_state.get(_SELECTED_APP_ROLE_KEY)
        or st.session_state.get(_LEGACY_SELECTED_ROLE_KEY)
    )

    with st.expander("Role dropdown debug", expanded=False):
        st.write("st.user.user_name", debug_context.get("st_user_name") or "Unavailable")
        st.write("SELECT CURRENT_USER()", debug_context.get("current_user") or "Unavailable")
        st.write("SELECT CURRENT_ROLE()", debug_context.get("current_role") or "Unavailable")
        st.write("Roles fetched from SHOW GRANTS", debug_context.get("show_grants_roles") or [])
        st.write("Final dropdown roles", debug_context.get("final_dropdown_roles") or [])
        st.write("selected_role", debug_context.get("selected_role") or "Unavailable")
        if debug_context.get("show_grants_error"):
            st.warning(debug_context["show_grants_error"])


def has_app_role(role_name: object) -> bool:
    """Check the selected app role first, then loaded viewer role grants."""
    requested_role = _clean_context_value(role_name).casefold()
    if not requested_role:
        return False

    selected_role = _clean_context_value(
        st.session_state.get(_SELECTED_APP_ROLE_KEY)
        or st.session_state.get("selected_role")
        or st.session_state.get(_LEGACY_SELECTED_ROLE_KEY)
    )
    if selected_role.casefold() == requested_role:
        return True

    viewer_roles = st.session_state.get("viewer_granted_roles") or st.session_state.get(
        "available_roles"
    ) or []
    return any(_clean_context_value(role).casefold() == requested_role for role in viewer_roles)
