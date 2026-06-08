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


def get_current_user(session) -> str:
    row = session.sql("SELECT CURRENT_USER() AS CURRENT_USER").to_pandas().iloc[0]
    return str(row["CURRENT_USER"]).strip()


def get_current_role(session) -> str:
    row = session.sql("SELECT CURRENT_ROLE() AS CURRENT_ROLE").to_pandas().iloc[0]
    return str(row["CURRENT_ROLE"]).strip()


@st.cache_data(show_spinner=False, ttl=300)
def get_available_roles_for_current_user(_session) -> list[str]:
    current_role = get_current_role(_session)

    try:
        roles_df = _session.sql("""
            SELECT VALUE::STRING AS ROLE_NAME
            FROM TABLE(
                FLATTEN(INPUT => PARSE_JSON(CURRENT_AVAILABLE_ROLES()))
            )
            ORDER BY ROLE_NAME
        """).to_pandas()
    except Exception as ex:
        st.warning(f"Unable to fetch Snowflake roles. Showing current role only. Error: {ex}")
        return [current_role] if current_role else []

    if roles_df.empty or "ROLE_NAME" not in roles_df.columns:
        available_roles: list[str] = []
    else:
        available_roles = sorted(
            {
                str(role_name or "").strip()
                for role_name in roles_df["ROLE_NAME"].tolist()
                if str(role_name or "").strip()
            }
        )

    if current_role and current_role not in available_roles:
        available_roles.append(current_role)
        available_roles = sorted(set(available_roles))

    return available_roles


def get_available_roles(session) -> tuple[list[str], str]:
    current_role = get_current_role(session)
    available_roles = get_available_roles_for_current_user(_session=session)
    if current_role and current_role not in available_roles:
        available_roles = sorted({*available_roles, current_role})
    if not available_roles:
        available_roles = [current_role] if current_role else []
    return available_roles, current_role


def get_selected_sf_role(session) -> str:
    available_roles, current_role = get_available_roles(session)
    selected_role = str(st.session_state.get("selected_sf_role") or "").strip()
    if selected_role and selected_role in available_roles:
        return selected_role
    return current_role


def get_current_user_context(session) -> UserContext:
    username = get_current_user(session)
    sf_role = str(st.session_state.get("selected_sf_role") or "").strip() or get_current_role(session)
    return UserContext(username=username, sf_role=sf_role)


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


def can_edit_claim(claim_status: str, assigned_to: object, username: object) -> bool:
    is_assigned_user = _normalize_identifier(assigned_to) == _normalize_identifier(username)
    return claim_status in {"MFQ Generated", "Assigned", "Rejected"} or (claim_status == "Assigned" and is_assigned_user)
