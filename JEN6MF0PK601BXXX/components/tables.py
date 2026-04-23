from __future__ import annotations

import html
from collections.abc import Callable

import pandas as pd
import streamlit as st


DASHBOARD_TABLE_COLS = [1.18, 2.65, 1.3, 1.1, 1.25, 1.2, 0.95]
CLAIMS_TABLE_COLS = [1.05, 2.45, 1.18, 1.02, 1.15, 1.08, 1.8]


STATUS_STYLES = {
    "MFQ Generated": "badge badge-status badge-blue",
    "Assigned": "badge badge-status badge-indigo",
    "Approved": "badge badge-status badge-green",
    "Rejected": "badge badge-status badge-red",
}

PRIORITY_STYLES = {
    "Critical": "badge badge-priority badge-red-soft",
    "High": "badge badge-priority badge-amber",
    "Medium": "badge badge-priority badge-blue-soft",
    "Low": "badge badge-priority badge-slate",
}


def _safe(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _format_date(value) -> str:
    if value is None or value == "":
        return ""
    try:
        return pd.to_datetime(value).strftime("%b %d,\n%Y")
    except Exception:
        return _safe(value)


def status_chip(value: str) -> str:
    css = STATUS_STYLES.get(str(value), "badge badge-status badge-slate")
    return f'<span class="{css}">{_safe(value)}</span>'


def priority_chip(value: str) -> str:
    css = PRIORITY_STYLES.get(str(value), "badge badge-priority badge-slate")
    return f'<span class="{css}">{_safe(value)}</span>'


def confidence_chip(value) -> str:
    try:
        numeric = float(value)
    except Exception:
        numeric = 0.0

    if numeric >= 90:
        css = "confidence-chip confidence-green"
    elif numeric >= 80:
        css = "confidence-chip confidence-amber"
    else:
        css = "confidence-chip confidence-red"

    return f'<span class="{css}"><span class="confidence-dot">•</span> {numeric:.0f}%</span>'


def _render_table_header(table_cols: list[float], show_regenerate: bool) -> None:
    header = st.columns(table_cols, vertical_alignment="center")
    labels = [
        "CLAIM ID",
        "PATIENT / DEFENDANT",
        "STATUS",
        "PRIORITY",
        "DATE\nREQUESTED",
        "AI\nCONFIDENCE",
        "ACTION" if not show_regenerate else "ACTION",
    ]
    for col, label in zip(header, labels):
        extra = " table-head-right" if "ACTION" in label else ""
        col.markdown(f'<div class="table-head{extra}">{label}</div>', unsafe_allow_html=True)


def _render_dashboard_action(col, claim_id: str, row_key: str, on_review: Callable[[str], None]) -> None:
    with col:
        st.markdown('<div class="table-action-inline">', unsafe_allow_html=True)
        if st.button("Review  →", key=f"review_{row_key}", use_container_width=True, type="tertiary"):
            on_review(claim_id)
        st.markdown('</div>', unsafe_allow_html=True)


def _render_claims_action(
    col,
    claim_id: str,
    row_key: str,
    can_regenerate: bool,
    on_review: Callable[[str], None],
    on_regenerate: Callable[[str], None] | None,
) -> None:
    left, right = col.columns([1.28, 0.82], gap="small")
    with left:
        if can_regenerate and on_regenerate is not None:
            st.markdown('<div class="table-regenerate-btn">', unsafe_allow_html=True)
            if st.button("⟳  Regenerate", key=f"regen_{row_key}", use_container_width=True, type="secondary"):
                on_regenerate(claim_id)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="action-spacer"></div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="table-action-inline">', unsafe_allow_html=True)
        if st.button("Review  →", key=f"review_{row_key}", use_container_width=True, type="tertiary"):
            on_review(claim_id)
        st.markdown('</div>', unsafe_allow_html=True)


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
        wrapper_class = "claims-table-shell has-regenerate" if show_regenerate else "claims-table-shell"
        st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)

        header_left, header_right = st.columns([4.65, 1.7], vertical_alignment="bottom")

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
            st.markdown('</div>', unsafe_allow_html=True)
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

        st.markdown('</div>', unsafe_allow_html=True)
