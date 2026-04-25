import pandas as pd
import streamlit as st


def render(_session, role: str, username: str):
    st.subheader("Admin / RBAC")

    if role != "Admin":
        st.warning("You are viewing this page in read-only mode. Switch to Admin role to manage access.")

    st.markdown("#### User & Role Management")
    users = pd.DataFrame(
        [
            {"USER": username, "TEAM": "Claims", "ROLE": role, "STATUS": "Active"},
            {"USER": "ANALYST_2", "TEAM": "Claims", "ROLE": "Claim Analyst", "STATUS": "Active"},
            {"USER": "FACULTY_1", "TEAM": "Medical", "ROLE": "Medical Faculty", "STATUS": "Active"},
            {"USER": "ADVICE_LEAD", "TEAM": "Advice", "ROLE": "Advice Team", "STATUS": "Inactive"},
        ]
    )
    st.dataframe(users, use_container_width=True)

    st.markdown("#### RBAC Matrix")
    matrix = pd.DataFrame(
        [
            {"PERMISSION": "View Claims", "Claim Analyst": "✅", "Advice Team": "✅", "Medical Faculty": "✅", "Admin": "✅"},
            {"PERMISSION": "Approve / Reject", "Claim Analyst": "✅", "Advice Team": "✅", "Medical Faculty": "✅", "Admin": "✅"},
            {"PERMISSION": "Role Assignment", "Claim Analyst": "❌", "Advice Team": "❌", "Medical Faculty": "❌", "Admin": "✅"},
            {"PERMISSION": "Report Export", "Claim Analyst": "✅", "Advice Team": "✅", "Medical Faculty": "✅", "Admin": "✅"},
        ]
    )
    st.dataframe(matrix, use_container_width=True, hide_index=True)

    st.markdown("#### Access Controls")
    c1, c2, c3 = st.columns(3)
    c1.toggle("Enable SSO Enforcement", value=True, disabled=role != "Admin")
    c2.toggle("MFA Required for Admin", value=True, disabled=role != "Admin")
    c3.toggle("Audit Log Alerts", value=True, disabled=role != "Admin")

    st.button("Save RBAC Changes", disabled=role != "Admin")
