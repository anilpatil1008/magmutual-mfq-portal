from __future__ import annotations

import streamlit as st
from utils.streamlit_compat import safe_dataframe

from repositories.admin_repository import get_assignment_queue, get_role_permissions, get_users_with_roles


def render(session, ctx) -> None:
    st.subheader("Administration")
    if ctx.sf_role != "Admin":
        st.error("Admin access is required.")
        return

    t1, t2, t3 = st.tabs(["Users", "Role Mappings", "Permissions"])

    with t1:
        safe_dataframe(get_users_with_roles(session), use_container_width=True)

    with t2:
        safe_dataframe(get_role_permissions(session), use_container_width=True)

    with t3:
        safe_dataframe(get_assignment_queue(session), use_container_width=True)
