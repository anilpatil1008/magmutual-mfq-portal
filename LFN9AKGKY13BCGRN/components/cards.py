from __future__ import annotations

import html
import streamlit as st


CARD_ICONS = {
    "Total Active Claims": "📁",
    "MFQ Generated": "🧠",
    "Assigned": "👥",
    "On Hold": "⏸️",
    "Approved": "✅",
    "Rejected": "⛔",
}


def render_kpi_cards(metrics: dict[str, int]) -> None:
    cards: list[str] = []
    for metric, value in metrics.items():
        icon = CARD_ICONS.get(metric, "📊")
        safe_metric = html.escape(str(metric))
        safe_value = html.escape(str(value))
        cards.append(
            "".join(
                [
                    '<article class="mm-card">',
                    '<div class="mm-card-main">',
                    f'<div class="mm-card-label">{safe_metric}</div>',
                    f'<div class="mm-card-value">{safe_value}</div>',
                    "</div>",
                    f'<div class="mm-card-icon" aria-hidden="true">{icon}</div>',
                    "</article>",
                ]
            )
        )

    kpi_html = f'<section class="mm-kpi-grid">{"".join(cards)}</section>'
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
