from __future__ import annotations

import html
from typing import Callable

import pandas as pd
import streamlit as st


DASHBOARD_TABLE_COLS = [1.25, 3.2, 1.45, 1.1, 1.35, 1.2, 0.9]
CLAIMS_TABLE_COLS = [1.15, 3.0, 1.4, 1.1, 1.2, 1.1, 1.9]


def _safe(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _format_date(value) -> str:
    if value is None or value == "":
        return ""
    try:
        dt = pd.to_datetime(value)
        if pd.isna(dt):
            return _safe(value)
        return dt.strftime("%b %d, %Y")
    except Exception:
        return _safe(value)


def status_chip(status: str) -> str:
    mapping = {
        "MFQ Generated": "chip chip-blue",
        "Assigned": "chip chip-blue",
        "Approved": "chip chip-green",
        "Rejected": "chip chip-red",
    }
    css = mapping.get(str(status), "chip chip-gray")
    return f'<span class="{css}">{_safe(status)}</span>'


def priority_chip(priority: str) -> str:
    mapping = {
        "Critical": "chip chip-red",
        "High": "chip chip-yellow",
        "Medium": "chip chip-blue",
        "Low": "chip chip-gray",
    }
    css = mapping.get(str(priority), "chip chip-gray")
    return f'<span class="{css}">{_safe(priority)}</span>'


def confidence_chip(score) -> str:
    value = float(score or 0)
    if value >= 90:
        css = "chip chip-green"
    elif value >= 80:
        css = "chip chip-yellow"
    else:
        css = "chip chip-red"
    return f'<span class="chip confidence-chip {css}">• {value:.0f}%</span>'


def _render_table_header(table_cols: list[float], show_regenerate: bool) -> None:
    header = st.columns(table_cols, vertical_alignment="center")
    header[0].markdown('<div class="table-head">CLAIM ID</div>', unsafe_allow_html=True)
    header[1].markdown('<div class="table-head">PATIENT / DEFENDANT</div>', unsafe_allow_html=True)
    header[2].markdown('<div class="table-head">STATUS</div>', unsafe_allow_html=True)
    header[3].markdown('<div class="table-head">PRIORITY</div>', unsafe_allow_html=True)
    header[4].markdown('<div class="table-head">DATE REQUESTED</div>', unsafe_allow_html=True)
    header[5].markdown('<div class="table-head">AI CONFIDENCE</div>', unsafe_allow_html=True)
    action_label = "ACTIONS" if show_regenerate else "ACTION"
    header[6].markdown(f'<div class="table-head table-head-right">{action_label}</div>', unsafe_allow_html=True)


def _render_dashboard_action(col, claim_id: str, row_key: str, on_review: Callable[[str], None]) -> None:
    with col:
        st.markdown('<div class="dashboard-action-wrap">', unsafe_allow_html=True)
        if st.button("Review  →", key=f"review_{row_key}", use_container_width=True, type="tertiary"):
            on_review(claim_id)


def _render_claims_action(
    col,
    claim_id: str,
    row_key: str,
    can_regenerate: bool,
    on_review: Callable[[str], None],
    on_regenerate: Callable[[str], None] | None,
) -> None:
    action_left, action_right = col.columns([1.05, 0.95], gap="small")
    with action_left:
        if can_regenerate and on_regenerate is not None:
            if st.button("↻  Regenerate", key=f"regen_{row_key}", use_container_width=True, type="secondary"):
                on_regenerate(claim_id)
        else:
            st.markdown('<div class="action-spacer"></div>', unsafe_allow_html=True)

    with action_right:
        if st.button("Review  →", key=f"review_{row_key}", use_container_width=True, type="tertiary"):
            on_review(claim_id)


def render_claims_table(
    queue_df,
    on_review: Callable[[str], None],
    on_regenerate: Callable[[str], None] | None = None,
    *,
    show_regenerate: bool = False,
    title: str = "Recent Claims",
    subtitle: str = "Latest claims submitted for assessment.",
    search_key: str = "claims_table_inline_search",
) -> None:
    table_cols = CLAIMS_TABLE_COLS if show_regenerate else DASHBOARD_TABLE_COLS

    st.markdown('<div class="claims-section-gap"></div>', unsafe_allow_html=True)

    with st.container(border=True):

        header_left, header_right = st.columns([4.7, 1.7], vertical_alignment="bottom")

        with header_left:
            st.markdown(
                f"""
                <div class="section-title section-title-sm">{_safe(title)}</div>
                <div class="section-subtitle">{_safe(subtitle)}</div>
                """,
                unsafe_allow_html=True,
            )

        with header_right:
            st.text_input(
                "Search claims",
                placeholder="Search by patient, file #...",
                label_visibility="collapsed",
                key=search_key,
            )

        st.markdown('<div class="table-divider"></div>', unsafe_allow_html=True)

        if queue_df.empty:
            st.info("No claims found")
            return

        _render_table_header(table_cols, show_regenerate)
        st.markdown('<div class="table-divider table-divider-tight"></div>', unsafe_allow_html=True)

        for idx, (_, row) in enumerate(queue_df.iterrows()):
            row_key = f"{row['CLAIM_ID']}_{idx}"
            cols = st.columns(table_cols, vertical_alignment="center")

            cols[0].markdown(
                f'<div class="claim-file-no">{_safe(row.get("FILE_NUMBER", row.get("CLAIM_ID", "")))}</div>',
                unsafe_allow_html=True,
            )
            cols[1].markdown(
                f"""
                <div class="claim-person-wrap">
                    <div class="claim-person-name">{_safe(row.get('PATIENT_NAME', ''))}</div>
                    <div class="claim-subtext">vs. {_safe(row.get('DEFENDANT_NAME', ''))}<br>({_safe(row.get('DEFENDANT_SPECIALTY', ''))})</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            cols[2].markdown(status_chip(row.get("STATUS", "")), unsafe_allow_html=True)
            cols[3].markdown(priority_chip(row.get("PRIORITY", "")), unsafe_allow_html=True)
            cols[4].markdown(
                f'<div class="table-value date-value">{_format_date(row.get("DATE_REQUESTED", ""))}</div>',
                unsafe_allow_html=True,
            )
            cols[5].markdown(confidence_chip(row.get("AI_CONFIDENCE", 0)), unsafe_allow_html=True)

            if show_regenerate:
                _render_claims_action(
                    cols[6],
                    row.get("CLAIM_ID", ""),
                    row_key,
                    bool(row.get("CAN_REGENERATE", False)),
                    on_review,
                    on_regenerate,
                )
            else:
                _render_dashboard_action(cols[6], row.get("CLAIM_ID", ""), row_key, on_review)

            st.markdown('<div class="table-divider table-divider-row"></div>', unsafe_allow_html=True)

