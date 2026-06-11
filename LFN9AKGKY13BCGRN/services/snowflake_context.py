from __future__ import annotations

import logging
import math
import os
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)

_EMPTY_CONTEXT_VALUES = {"", "none", "null", "nan", "n/a"}
_SELECTED_APP_ROLE_KEY = "selected_app_role"
# st.session_state.selected_role is the canonical app-level viewer selected role.
# It is UI/display context only; Streamlit in Snowflake owner-rights apps must not
# issue USE ROLE for this value because SQL continues to run with app privileges.
_CANONICAL_SELECTED_ROLE_KEY = "selected_role"
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


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        cleaned = _clean_context_value(value)
        if not cleaned:
            continue
        normalized = cleaned.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(cleaned)
    return deduped


def _dedupe_sorted(values: list[str]) -> list[str]:
    return sorted(_dedupe_preserve_order(values))


def _extract_column_values(df: Any, *candidate_names: str) -> list[str]:
    normalized_candidates = {name.casefold() for name in candidate_names}
    for column in getattr(df, "columns", []):
        if str(column).casefold() in normalized_candidates:
            return [_clean_context_value(value) for value in df[column].tolist()]
    return []


def _row_to_dict(row: object) -> dict[str, object]:
    if row is None:
        return {}
    if hasattr(row, "as_dict"):
        try:
            return row.as_dict()
        except Exception:
            pass
    if hasattr(row, "to_dict"):
        try:
            return row.to_dict()
        except Exception:
            pass
    try:
        return dict(row)
    except Exception:
        return {}


def _get_first_row_value(row: object, *candidate_names: str) -> str:
    row_dict = _row_to_dict(row)
    normalized_candidates = {name.casefold() for name in candidate_names}
    for key, value in row_dict.items():
        if str(key).casefold() in normalized_candidates:
            return _clean_context_value(value)
    return ""


def _get_row_value(row: object, *candidate_names: str) -> str:
    row_dict = _row_to_dict(row)
    normalized_candidates = {name.casefold() for name in candidate_names}
    for key, value in row_dict.items():
        if str(key).casefold() in normalized_candidates:
            return _clean_context_value(value)
    try:
        return _clean_context_value(row[0])
    except Exception:
        return ""


def quote_snowflake_identifier(identifier: str) -> str:
    """Return a safely double-quoted Snowflake identifier."""
    return '"' + str(identifier or "").replace('"', '""') + '"'


def quote_snowflake_literal(value: str) -> str:
    """Return a safely single-quoted Snowflake string literal."""
    return "'" + str(value or "").replace("'", "''") + "'"


def _get_streamlit_user_value(attribute_name: str) -> str:
    """Read viewer metadata from Streamlit identity via st.user."""
    try:
        user = getattr(st, "user", None)
    except Exception as ex:  # pragma: no cover - runtime compatibility guard
        _debug_log("Unable to read st.user.%s: %s", attribute_name, ex)
        return ""

    if user is None:
        return ""

    value = ""
    try:
        value = getattr(user, attribute_name, "")
    except Exception as ex:  # pragma: no cover - runtime compatibility guard
        _debug_log("Unable to read st.user.%s attribute: %s", attribute_name, ex)

    if not value and hasattr(user, "get"):
        try:
            value = user.get(attribute_name, "")
        except Exception as ex:  # pragma: no cover - runtime compatibility guard
            _debug_log("Unable to read st.user[%s]: %s", attribute_name, ex)

    return _clean_context_value(value)


def _get_current_user_from_sql(session) -> str:
    try:
        row = session.sql("SELECT CURRENT_USER() AS USER_NAME").to_pandas().iloc[0]
    except Exception as ex:
        _debug_log("Unable to fetch CURRENT_USER(): %s", ex)
        return ""
    return _get_first_row_value(row, "USER_NAME", "CURRENT_USER")


def get_viewer_username(session=None) -> str:
    """Return the Streamlit viewer username, preserving local SQL fallback."""
    for attribute_name in ("user_name", "username", "login_name"):
        username = _get_streamlit_user_value(attribute_name)
        if username:
            return username

    if session is not None:
        return _get_current_user_from_sql(session)

    return ""


def get_viewer_email() -> str:
    """Return the Streamlit viewer email when Streamlit identity provides it."""
    return _get_streamlit_user_value("email")


def get_viewer_user(session=None) -> dict[str, str]:
    """Return the actual Streamlit viewer identity, never relying only on SQL.

    In Snowflake Streamlit warehouse runtime, CURRENT_USER() is owner/session
    context. st.user.user_name and st.user.email are therefore the authoritative
    viewer identity fields when present.
    """
    username = get_viewer_username(session)

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
        "email": get_viewer_email() or "N/A",
    }


def get_current_owner_role(session) -> str:
    """Return CURRENT_ROLE(), which is the runtime/app owner role.

    In Streamlit in Snowflake owner-rights mode, CURRENT_ROLE() is not the
    interactive viewer's selected role. It is only an internal fallback/context
    value and must not be displayed as the viewer role.
    """
    try:
        row = session.sql("SELECT CURRENT_ROLE() AS ROLE_NAME").to_pandas().iloc[0]
    except Exception as ex:
        _debug_log("Unable to fetch CURRENT_ROLE(): %s", ex)
        return ""
    return _get_first_row_value(row, "ROLE_NAME", "CURRENT_ROLE")


def get_runtime_owner_role(session) -> str:
    """Alias for the owner-rights runtime role context."""
    return get_current_owner_role(session)


def get_viewer_default_role(session, viewer_user: object) -> str:
    """Return the Snowflake default role configured for the Streamlit viewer."""
    cleaned_username = _clean_context_value(viewer_user)
    if not cleaned_username or cleaned_username == "Unknown":
        return ""

    try:
        safe_user_literal = quote_snowflake_literal(cleaned_username)
        session.sql(f"SHOW USERS LIKE {safe_user_literal}").collect()
        rows = session.sql(
            """
            SELECT "default_role" AS DEFAULT_ROLE
            FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
            WHERE UPPER("name") = UPPER(?)
            """,
            params=[cleaned_username],
        ).collect()
    except TypeError:
        try:
            rows = session.sql(f"""
                SELECT "default_role" AS DEFAULT_ROLE
                FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
                WHERE UPPER("name") = UPPER({quote_snowflake_literal(cleaned_username)})
                """).collect()
        except Exception as ex:
            _debug_log("Unable to fetch default role for %s: %s", cleaned_username, ex)
            return ""
    except Exception as ex:
        _debug_log("Unable to fetch default role for %s: %s", cleaned_username, ex)
        return ""

    if rows:
        return _get_row_value(rows[0], "DEFAULT_ROLE", "default_role")
    return ""


def _read_show_grants_roles(session) -> list[str]:
    rows = session.sql("""
        SELECT *
        FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
    """).collect()

    roles: list[str] = []
    for row in rows:
        role_name = _get_row_value(row, "role", "ROLE", "name", "NAME", "ROLE_NAME")
        if role_name:
            roles.append(role_name)
    return _dedupe_sorted(roles)


def _get_existing_role_list(viewer_username: str = "") -> list[str]:
    """Return already-loaded app roles only for the current viewer session."""
    cached_username = _clean_context_value(
        st.session_state.get("viewer_role_context_username")
    )
    cleaned_username = _clean_context_value(viewer_username)
    if (
        cached_username
        and cleaned_username
        and cached_username.casefold() != cleaned_username.casefold()
    ):
        return []

    existing_roles = (
        st.session_state.get("available_roles")
        or st.session_state.get("viewer_granted_roles")
        or []
    )
    if not isinstance(existing_roles, (list, tuple, set)):
        return []
    return _dedupe_preserve_order(list(existing_roles))


def _get_roles_from_show_grants(session, viewer_username: str) -> list[str]:
    cleaned_username = _clean_context_value(viewer_username)
    if not cleaned_username or cleaned_username == "Unknown":
        return []

    safe_user = quote_snowflake_identifier(cleaned_username)
    try:
        session.sql(f"SHOW GRANTS TO USER {safe_user}").collect()
        return _read_show_grants_roles(session)
    except Exception as ex:
        _debug_log("Unable to fetch SHOW GRANTS roles for %s: %s", cleaned_username, ex)
        return []


def get_viewer_granted_roles(session) -> list[str]:
    """Return roles granted to the Streamlit viewer, with safe fallbacks.

    SHOW GRANTS is scoped to st.user.user_name (not CURRENT_ROLE()). If the
    owner-rights runtime cannot inspect user grants, reuse any already-loaded
    role list and only then fall back internally to the runtime owner role.
    """
    viewer_username = _clean_context_value(get_viewer_username(session))

    roles = _get_roles_from_show_grants(session, viewer_username)
    if roles:
        st.session_state["viewer_role_context_username"] = viewer_username
        return _dedupe_sorted(roles)

    existing_roles = _get_existing_role_list(viewer_username)
    if existing_roles:
        return existing_roles

    owner_role = get_current_owner_role(session)
    return [owner_role] if owner_role else ["Unknown"]


def _get_existing_selected_role() -> str:
    for state_key in (
        _CANONICAL_SELECTED_ROLE_KEY,
        _SELECTED_APP_ROLE_KEY,
        _LEGACY_SELECTED_ROLE_KEY,
    ):
        selected_role = _clean_context_value(st.session_state.get(state_key))
        if selected_role:
            return selected_role
    return ""


def get_role_dropdown_options(session) -> list[str]:
    """Return viewer-selectable UI roles without treating CURRENT_ROLE as viewer.

    The dropdown is built from viewer grants, the viewer default role, and any
    already-fetched app role list. The runtime owner role is appended only as the
    final internal fallback so the widget can render during local/limited-perm
    execution.
    """
    viewer_username = _clean_context_value(get_viewer_username(session))
    granted_roles = get_viewer_granted_roles(session)
    default_role = _clean_context_value(
        get_viewer_default_role(session, viewer_username)
    )
    selected_role = (
        _get_existing_selected_role()
        if st.session_state.get("role_default_initialized")
        else ""
    )

    role_options = _dedupe_preserve_order(
        [
            *granted_roles,
            default_role,
            *_get_existing_role_list(viewer_username),
            selected_role,
        ]
    )

    if not role_options:
        owner_role = _clean_context_value(get_current_owner_role(session))
        role_options = [owner_role] if owner_role else ["Unknown"]

    return role_options


def set_selected_app_role(role_name: object) -> str:
    """Store the app-level selected role without switching SQL execution role."""
    selected_role = _clean_context_value(role_name) or "Unknown"
    st.session_state["role_default_initialized"] = True
    st.session_state[_SELECTED_APP_ROLE_KEY] = selected_role
    st.session_state[_CANONICAL_SELECTED_ROLE_KEY] = selected_role
    # Keep the legacy key synchronized so existing cache scopes and page state
    # continue to behave exactly as before while the canonical key moves to
    # selected_app_role.
    st.session_state[_LEGACY_SELECTED_ROLE_KEY] = selected_role
    st.session_state["sf_role"] = selected_role
    return selected_role


def get_initial_selected_role(session, roles: list[str]) -> str:
    """Resolve the initial dropdown role without issuing USE ROLE."""
    role_options = _dedupe_sorted(roles)
    if not role_options:
        return ""

    if st.session_state.get("role_default_initialized"):
        selected_role = _get_existing_selected_role()
        if selected_role:
            if selected_role not in role_options:
                role_options.append(selected_role)
            return selected_role

    viewer_username = _clean_context_value(get_viewer_username(session))
    default_role = _clean_context_value(
        get_viewer_default_role(session, viewer_username)
    )
    if default_role:
        if default_role not in role_options:
            role_options.append(default_role)
        return default_role

    selected_role = _get_existing_selected_role()
    if selected_role:
        if selected_role not in role_options:
            role_options.append(selected_role)
        return selected_role

    viewer_granted_roles = [role for role in role_options if role != "Unknown"]
    if viewer_granted_roles:
        return viewer_granted_roles[0]

    current_role = _clean_context_value(get_current_owner_role(session))
    if current_role:
        return current_role

    return role_options[0]


def get_selected_app_role(session) -> str:
    """Resolve and persist the selected app-level role for UI decisions.

    st.session_state.selected_role is the app-level viewer selected role. It is
    deliberately independent from CURRENT_ROLE() in owner-rights execution.
    """
    role_options = get_role_dropdown_options(session)
    selected_role = get_initial_selected_role(session, role_options)

    if selected_role:
        return set_selected_app_role(selected_role)

    owner_role = get_current_owner_role(session)
    if owner_role:
        return set_selected_app_role(owner_role)

    return set_selected_app_role("Unknown")


def get_viewer_selected_role(session=None) -> str:
    """Return the persisted app-level viewer selected role."""
    selected_role = _get_existing_selected_role()
    if selected_role:
        return selected_role
    if session is None:
        return ""
    return get_selected_app_role(session)


def has_app_role(role_name: object) -> bool:
    """Check the selected app role first, then loaded viewer role grants."""
    requested_role = _clean_context_value(role_name).casefold()
    if not requested_role:
        return False

    selected_role = _clean_context_value(
        st.session_state.get(_CANONICAL_SELECTED_ROLE_KEY)
        or st.session_state.get(_SELECTED_APP_ROLE_KEY)
        or st.session_state.get(_LEGACY_SELECTED_ROLE_KEY)
    )
    if selected_role.casefold() == requested_role:
        return True

    viewer_roles = (
        st.session_state.get("viewer_granted_roles")
        or st.session_state.get("available_roles")
        or []
    )
    return any(
        _clean_context_value(role).casefold() == requested_role for role in viewer_roles
    )
