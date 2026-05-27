from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class UserContext:
    username: str
    app_role: str
    sf_role: str


APP_ROLES = [
    "Claims Analyst",
    "Advice Team",
    "Medical Faculty",
    "Executive",
    "Admin",
]

ROLE_NAV = {
    "Claims Analyst": ["Dashboard", "Claims", "Claim Details", "Reports"],
    "Advice Team": ["Dashboard", "Claims", "Claim Details", "Reports"],
    "Medical Faculty": ["Dashboard", "Claims", "Claim Details"],
    "Executive": ["Dashboard", "Reports"],
    "Admin": ["Dashboard", "Claims", "Reports", "Admin"],
}


def get_current_user(session) -> str:
    row = session.sql("SELECT CURRENT_USER() AS CURRENT_USER").to_pandas().iloc[0]
    return str(row["CURRENT_USER"]).strip()


def get_current_role(session) -> str:
    row = session.sql("SELECT CURRENT_ROLE() AS CURRENT_ROLE").to_pandas().iloc[0]
    return str(row["CURRENT_ROLE"]).strip()


@st.cache_data(show_spinner=False, ttl=300)
def _fetch_assigned_roles_for_user(session, username: str) -> list[str]:
    grants_df = session.sql(f'SHOW GRANTS TO USER "{username}"').to_pandas()
    if grants_df.empty:
        return []

    role_values: list[str] = []
    for column in grants_df.columns:
        if str(column).strip().upper() in {"ROLE", "GRANTED_ROLE"}:
            role_values.extend(grants_df[column].tolist())

    deduped_roles = sorted({str(value or "").strip() for value in role_values if str(value or "").strip()})
    return deduped_roles


def get_available_roles_for_current_user(session) -> list[str]:
    username = get_current_user(session)
    current_role = get_current_role(session)

    try:
        assigned_roles = _fetch_assigned_roles_for_user(session, username)
    except Exception:
        return [current_role] if current_role else []

    if not assigned_roles:
        return [current_role] if current_role else []

    if current_role and current_role not in assigned_roles:
        assigned_roles.append(current_role)
        assigned_roles = sorted(set(assigned_roles))
    return assigned_roles


def get_available_roles(session) -> tuple[list[str], str]:
    current_role = get_current_role(session)
    available_roles = get_available_roles_for_current_user(session)
    if current_role and current_role not in available_roles:
        available_roles = sorted({*available_roles, current_role})
    if not available_roles:
        available_roles = [current_role] if current_role else []
    return available_roles, current_role


def get_current_user_context(session) -> UserContext:
    username = get_current_user(session)
    sf_role = get_current_role(session)

    if "app_role" not in st.session_state:
        st.session_state.app_role = "Claims Analyst"

    return UserContext(
        username=username,
        app_role=st.session_state.app_role,
        sf_role=sf_role,
    )


def set_active_role(new_role: str) -> None:
    st.session_state.app_role = new_role


def allowed_pages(app_role: str) -> list[str]:
    return ROLE_NAV.get(app_role, ["Dashboard"])


def can_edit_claim(app_role: str, claim_status: str, assigned_to: str | None, username: str) -> bool:
    if app_role in {"Claims Analyst", "Advice Team", "Admin"}:
        return claim_status in {"MFQ Generated", "Assigned", "Rejected"}
    if app_role == "Medical Faculty":
        return claim_status == "Assigned" and (assigned_to or "").upper() == username.upper()
    return False
