import streamlit as st


def render_kpi_cards(metrics: dict) -> None:
    cols = st.columns(len(metrics))
    for idx, (label, value) in enumerate(metrics.items()):
        with cols[idx]:
            st.markdown(
                f"""
                <div class='kpi-card'>
                    <div class='kpi-label'>{label}</div>
                    <div class='kpi-value'>{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_claim_header(claim: dict) -> None:
    st.markdown(
        f"""
        <div class='claim-header-card'>
            <div class='claim-title'>Claim {claim['CLAIM_ID']} - {claim['PATIENT_NAME']}</div>
            <div class='claim-grid'>
                <div><b>Defendant:</b> {claim['DEFENDANT_NAME']}</div>
                <div><b>File Number:</b> {claim['FILE_NUMBER']}</div>
                <div><b>Specialty:</b> {claim['SPECIALTY']}</div>
                <div><b>Date Requested:</b> {claim['DATE_REQUESTED']}</div>
                <div><b>Contact:</b> {claim['CONTACT_DETAILS']}</div>
                <div><b>Status:</b> {claim['STATUS']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
