from __future__ import annotations

import streamlit as st

from repositories.admin_repository import get_assignment_queue, get_role_permissions, get_users_with_roles


def render(session, ctx) -> None:
    st.subheader("Administration")
    if ctx.app_role != "Admin":
        st.error("Admin access is required.")
        return

    t1, t2, t3 = st.tabs(["Users", "Role Mappings", "Permissions"])

    with t1:
        st.dataframe(get_users_with_roles(session), use_container_width=True)

    with t2:
        st.dataframe(get_role_permissions(session), use_container_width=True)

    with t3:
        st.dataframe(get_assignment_queue(session), use_container_width=True)
