from __future__ import annotations

import streamlit as st

from services.snowflake_service import safe_collect_df


def render(session, ctx) -> None:
    st.subheader("Administration")
    if ctx.app_role != "Admin":
        st.error("Admin access is required.")
        return

    t1, t2, t3 = st.tabs(["Users", "Role Mappings", "Permissions"])

    with t1:
        users = safe_collect_df(
            session,
            """
            SELECT u.USERNAME, u.DISPLAY_NAME, u.IS_ACTIVE, r.ROLE_NAME AS APP_ROLE
            FROM APP_USER u
            LEFT JOIN APP_USER_ROLE ur ON ur.USER_ID = u.USER_ID AND ur.IS_ACTIVE = TRUE
            LEFT JOIN APP_ROLE r ON r.ROLE_ID = ur.ROLE_ID
            ORDER BY u.USERNAME
            """,
        )
        st.dataframe(users, use_container_width=True)

    with t2:
        mapping = safe_collect_df(
            session,
            """
            SELECT r.ROLE_NAME, p.PERMISSION_CODE, p.PERMISSION_NAME, rp.IS_ACTIVE
            FROM APP_ROLE_PERMISSION rp
            JOIN APP_ROLE r ON r.ROLE_ID = rp.ROLE_ID
            JOIN APP_PERMISSION p ON p.PERMISSION_ID = rp.PERMISSION_ID
            ORDER BY r.ROLE_NAME, p.PERMISSION_CODE
            """,
        )
        st.dataframe(mapping, use_container_width=True)

    with t3:
        assignments = safe_collect_df(session, "SELECT * FROM MFQ_ASSIGNMENT_QUEUE_VW ORDER BY ASSIGNED_AT DESC")
        st.dataframe(assignments, use_container_width=True)
