from __future__ import annotations

from dataclasses import dataclass
import math

import streamlit as st

from services.snowflake_context import (
    get_current_owner_role,
    get_role_dropdown_options,
    get_selected_app_role,
    get_viewer_granted_roles,
    get_viewer_user,
)


@dataclass(frozen=True)
class UserContext:
    username: str
    sf_role: str
    display_name: str = "User"
    email: str = "N/A"


def get_current_user(session) -> str:
    return get_viewer_user(session).get("username", "Unknown")


def get_current_user_email() -> str:
    return get_viewer_user().get("email", "N/A")


def get_current_user_display_name(username: str) -> str:
    return get_viewer_user().get("display_name") or username


def get_current_role(session) -> str:
    return get_current_owner_role(session)


def get_available_roles_for_dropdown(session) -> list[str]:
    return get_role_dropdown_options(session)


def get_available_roles_for_current_user(_session) -> list[str]:
    return get_viewer_granted_roles(_session)


def get_available_roles(session) -> tuple[list[str], str]:
    current_role = get_current_role(session)
    available_roles = get_role_dropdown_options(session)
    st.session_state["viewer_granted_roles"] = available_roles
    return available_roles, current_role


def get_selected_sf_role(session) -> str:
    return get_selected_app_role(session)


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
    cache_scope = str(
        st.session_state.get("selected_app_role")
        or st.session_state.get("selected_sf_role")
        or "default"
    )
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
