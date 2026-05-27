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


@st.cache_data(show_spinner=False, ttl=300)
def _fetch_assigned_roles_for_user(session, username: str) -> list[str]:
    grants_df = session.sql(f"SHOW GRANTS TO USER {username}").to_pandas()
    if grants_df.empty:
        return []

    column_candidates = ["GRANTED_ROLE", "ROLE", "NAME"]
    role_column = next((column for column in column_candidates if column in grants_df.columns), None)
    if not role_column:
        return []

    roles: list[str] = []
    for value in grants_df[role_column].tolist():
        role = str(value or "").strip()
        if role and role not in roles:
            roles.append(role)
    return roles


def get_available_roles(session) -> tuple[list[str], str]:
    current = session.sql("SELECT CURRENT_USER() AS USERNAME, CURRENT_ROLE() AS SF_ROLE").to_pandas().iloc[0]
    username = str(current["USERNAME"])
    current_role = str(current["SF_ROLE"])

    try:
        assigned_roles = _fetch_assigned_roles_for_user(session, username)
        if not assigned_roles:
            return [current_role], current_role
        if current_role not in assigned_roles:
            assigned_roles = [current_role, *assigned_roles]
        return assigned_roles, current_role
    except Exception:
        return [current_role], current_role


def get_current_user_context(session) -> UserContext:
    row = session.sql("SELECT CURRENT_USER() AS USERNAME, CURRENT_ROLE() AS SF_ROLE").to_pandas().iloc[0]

    if "app_role" not in st.session_state:
        st.session_state.app_role = "Claims Analyst"

    return UserContext(
        username=str(row["USERNAME"]),
        app_role=st.session_state.app_role,
        sf_role=str(row["SF_ROLE"]),
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
