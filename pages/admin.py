from __future__ import annotations

import streamlit as st

from services.snowflake_service import safe_collect_df


def render(session, ctx) -> None:
    st.subheader("Administration")
    if ctx.app_role != "Admin":
        st.error("Admin access is required.")
        return

    t1, t2, t3 = st.tabs(["Users", "Role Mappings", "Routing Config"])

    with t1:
        users = safe_collect_df(session, "SELECT USERNAME, APP_ROLE, IS_ACTIVE FROM MFQ_APP_USERS ORDER BY USERNAME")
        st.dataframe(users, use_container_width=True)

    with t2:
        mapping = safe_collect_df(session, "SELECT APP_ROLE, PAGE_KEY, IS_ALLOWED FROM MFQ_ROLE_PAGE_ACCESS ORDER BY APP_ROLE, PAGE_KEY")
        st.dataframe(mapping, use_container_width=True)

    with t3:
        routing = safe_collect_df(session, "SELECT RULE_ID, SPECIALTY, DEFAULT_FACULTY, IS_ACTIVE FROM MFQ_ASSIGNMENT_RULES")
        st.dataframe(routing, use_container_width=True)
