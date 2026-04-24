import streamlit as st

from components.filters import render_claim_filters
from components.tables import render_claims_table
from services.snowflake_service import get_claims


def render(session, role: str, username: str):
    st.subheader("Claims")
    search, status, _ = render_claim_filters(prefix="claims")
    claims = get_claims(session, role, username, search=search, status=status)
    render_claims_table(claims, key_prefix="claims")
