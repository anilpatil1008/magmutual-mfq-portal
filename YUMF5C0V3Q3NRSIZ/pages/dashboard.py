import streamlit as st

from components.cards import render_kpi_cards
from components.filters import render_claim_filters
from components.tables import render_claims_table
from services.snowflake_service import get_claims, get_dashboard_metrics


def render(session, role: str, username: str):
    st.subheader("Dashboard")
    metrics = get_dashboard_metrics(session, role, username)
    render_kpi_cards(metrics)

    st.markdown("### Recent Claims")
    search, status, report_clicked = render_claim_filters(prefix="dash")
    claims = get_claims(session, role, username, search=search, status=status)
    render_claims_table(claims.head(20), key_prefix="dash")

    if report_clicked:
        st.success("Report generation started.")
