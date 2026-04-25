from __future__ import annotations

import html

import streamlit as st

CARD_ICONS = {
    "Total Active Claims": "📄",
    "MFQ Generated": "◉",
    "Assigned": "◔",
    "Approved": "✓",
    "Rejected": "⨯",
}


def render_kpi_cards(metrics: dict[str, int]) -> None:
    cards: list[str] = []
    for metric, value in metrics.items():
        icon = CARD_ICONS.get(metric, "◌")
        safe_metric = html.escape(str(metric))
        safe_value = html.escape(str(value))
        cards.append(
            "".join(
                [
                    '<article class="mm-card">',
                    '<div class="mm-card-main">',
                    f'<div class="mm-card-label">{safe_metric}</div>',
                    f'<div class="mm-card-value">{safe_value}</div>',
                    '</div><div class="mm-card-icon-wrap">',
                    f'<div class="mm-card-icon" aria-hidden="true">{icon}</div>',
                    "</div></article>",
                ]
            )
        )

    st.markdown(f'<section class="mm-kpi-grid">{"".join(cards)}</section>', unsafe_allow_html=True)


def render_claim_header(claim: dict) -> None:
    st.markdown(
        f"""
        <section class="mm-claim-header">
            <div class="mm-claim-title-row">
                <h3>{html.escape(str(claim.get('PATIENT_NAME', 'Unknown Patient')))} vs {html.escape(str(claim.get('DEFENDANT_NAME', 'Unknown Defendant')))}</h3>
                <div class="mm-claim-tags">{html.escape(str(claim.get('STATUS', '-')))} · {html.escape(str(claim.get('PRIORITY', '-')))}</div>
            </div>
            <div class="mm-claim-grid">
                <div><span>File Number</span><strong>{html.escape(str(claim.get('CLAIM_ID', '-')))}</strong></div>
                <div><span>Defendant Specialty</span><strong>{html.escape(str(claim.get('SPECIALTY', '-')))}</strong></div>
                <div><span>Date Requested</span><strong>{html.escape(str(claim.get('DATE_REQUESTED', '-')))}</strong></div>
                <div><span>Reviewer</span><strong>{html.escape(str(claim.get('ASSIGNED_TO', '-')))}</strong></div>
                <div><span>MagMutual Contact</span><strong>{html.escape(str(claim.get('ASSIGNED_TO', '-')))}</strong></div>
                <div><span>Contact Email</span><strong>{html.escape(str(claim.get('ASSIGNED_TO', '-')))}@magmutual.com</strong></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
