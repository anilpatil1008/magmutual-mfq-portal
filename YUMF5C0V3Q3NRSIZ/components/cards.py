from __future__ import annotations

import html
from textwrap import dedent

import streamlit as st


CARD_ICONS = {
    "Total Active Claims": "📁",
    "MFQ Generated": "🧠",
    "Assigned": "👥",
    "Approved": "✅",
    "Rejected": "⛔",
}


def render_kpi_cards(metrics: dict[str, int]) -> None:
    cards = []
    for metric, value in metrics.items():
        icon = CARD_ICONS.get(metric, "📊")
        cards.append(
            dedent(
                f"""
                <div class="mm-card">
                    <div class="mm-card-main">
                        <div class="mm-card-label">{html.escape(metric)}</div>
                        <div class="mm-card-value">{html.escape(str(value))}</div>
                    </div>
                    <div class="mm-card-icon" aria-hidden="true">{icon}</div>
                </div>
                """
            ).strip()
        )

    kpi_html = dedent(
        f"""
        <section class="mm-kpi-grid">
            {''.join(cards)}
        </section>
        """
    ).strip()

    st.markdown(kpi_html, unsafe_allow_html=True)


def render_claim_header(claim: dict) -> None:
    st.markdown(
        f"""
        <section class="mm-claim-header">
            <h3>{html.escape(str(claim.get('CLAIM_ID', 'Unknown Claim')))} · {html.escape(str(claim.get('PATIENT_NAME', 'Unknown Patient')))}</h3>
            <div class="mm-claim-grid">
                <div><strong>Defendant</strong><br>{html.escape(str(claim.get('DEFENDANT_NAME', '-')))}</div>
                <div><strong>File Number</strong><br>{html.escape(str(claim.get('FILE_NUMBER', '-')))}</div>
                <div><strong>Specialty</strong><br>{html.escape(str(claim.get('SPECIALTY', '-')))}</div>
                <div><strong>Date Requested</strong><br>{html.escape(str(claim.get('DATE_REQUESTED', '-')))}</div>
                <div><strong>Assigned To</strong><br>{html.escape(str(claim.get('ASSIGNED_TO', '-')))}</div>
                <div><strong>Priority</strong><br>{html.escape(str(claim.get('PRIORITY', '-')))}</div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
