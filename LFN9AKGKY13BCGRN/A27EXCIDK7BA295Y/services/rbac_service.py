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
