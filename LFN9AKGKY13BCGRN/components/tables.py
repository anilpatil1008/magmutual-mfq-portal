from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from components.badges import priority_badge, status_badge


VISIBLE_COLUMNS = [
    "CLAIM_ID",
    "PATIENT_NAME",
    "DEFENDANT_NAME",
    "STATUS",
    "PRIORITY",
    "DATE_REQUESTED",
    "ASSIGNED_TO",
]

ENTERPRISE_COLUMNS = [
    "CLAIM_ID",
    "PATIENT_NAME",
    "DEFENDANT_NAME",
    "STATUS",
    "PRIORITY",
    "DATE_REQUESTED",
    "AI_CONFIDENCE",
]
RECENT_CLAIMS_COLUMN_WIDTHS = [14, 26, 14, 10, 14, 10, 18]

def _normalize_slug(value: Any) -> str:
    text = str(value or "unknown").strip().lower().replace(" ", "-")
    return "".join(ch for ch in text if ch.isalnum() or ch == "-") or "unknown"


def _format_date(value: Any) -> str:
    if value is None:
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime("%b %d, %Y")
    as_text = str(value).strip()
    if not as_text:
        return "—"
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(as_text[:19], fmt).strftime("%b %d, %Y")
        except ValueError:
            continue
    return as_text


def _status_badge_html(status: Any) -> str:
    label = str(status or "Unknown")
    tone = _normalize_slug(label)
    return f"<span class='status-badge status-{tone}'>{escape(label)}</span>"


def _priority_badge_html(priority: Any) -> str:
    label = str(priority or "Unknown")
    tone = _normalize_slug(label)
    return f"<span class='priority-badge priority-{tone}'>{escape(label)}</span>"


def _confidence_badge_html(confidence: Any) -> str:
    if confidence is None or str(confidence).strip() == "":
        return "<span class='confidence-badge confidence-na'>● N/A</span>"

    try:
        score = float(confidence)
    except (TypeError, ValueError):
        return "<span class='confidence-badge confidence-na'>● N/A</span>"

    if 0 <= score <= 1:
        score *= 100
    score = max(0.0, min(score, 100.0))

    if score >= 90:
        band = "high"
    elif score >= 75:
        band = "medium"
    else:
        band = "low"

    return f"<span class='confidence-badge confidence-{band}'>● {score:.0f}%</span>"


def _run_regeneration(claim_id: str, row: pd.Series) -> tuple[bool, str]:
    callback = st.session_state.get("regenerate_mfq_callback")
    if not callable(callback):
        return False, "Unable to regenerate MFQ. Please try again or contact support."

    try:
        result = callback(claim_id=claim_id, row=row.to_dict())
    except Exception:
        return False, "Unable to regenerate MFQ. Please try again or contact support."

    if isinstance(result, bool):
        return (
            (True, "MFQ regenerated successfully.")
            if result
            else (False, "Unable to regenerate MFQ. Please try again or contact support.")
        )

    if isinstance(result, dict):
        ok = bool(result.get("success", False))
        message = str(
            result.get(
                "message",
                "MFQ regenerated successfully." if ok else "Unable to regenerate MFQ. Please try again or contact support.",
            )
        )
        return ok, message

    return True, "MFQ regenerated successfully."


def _sort_recent_claims(df: pd.DataFrame, sort_column: str, sort_ascending: bool) -> pd.DataFrame:
    if sort_column not in df.columns:
        return df

    if sort_column == "DATE_REQUESTED":
        sort_values = pd.to_datetime(df[sort_column], errors="coerce")
    elif sort_column == "AI_CONFIDENCE":
        sort_values = pd.to_numeric(df[sort_column], errors="coerce")
    else:
        sort_values = df[sort_column].astype(str).str.lower()

    return df.assign(_sort_value=sort_values).sort_values(
        by=["_sort_value", "CLAIM_ID"],
        ascending=[sort_ascending, True],
        na_position="last",
    ).drop(columns=["_sort_value"], errors="ignore")


def render_claims_table(df: pd.DataFrame, key_prefix: str = "claims") -> None:
    if df.empty:
        st.info("No claims found for this filter context.")
        return

    show_df = df.copy()
    show_df = show_df[[c for c in VISIBLE_COLUMNS if c in show_df.columns]]

    if "STATUS" in show_df.columns:
        show_df["STATUS"] = show_df["STATUS"].apply(lambda x: status_badge(str(x)))
    if "PRIORITY" in show_df.columns:
        show_df["PRIORITY"] = show_df["PRIORITY"].apply(lambda x: priority_badge(str(x)))

    rows = []
    for _, row in show_df.iterrows():
        claim_id = row.get("CLAIM_ID", "")
        btn_key = f"{key_prefix}_open_{claim_id}"
        if st.button(f"Review {claim_id}", key=btn_key):
            st.session_state.selected_claim_id = claim_id
            st.session_state.active_page = "Claim Details"
            st.rerun()

        row_html = "".join([f"<td>{value}</td>" for value in row.values])
        rows.append(f"<tr>{row_html}</tr>")

    head_html = "".join([f"<th>{h}</th>" for h in show_df.columns])
    table_html = f"<table class='mm-table'><thead><tr>{head_html}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)


def render_recent_claims_table(df: pd.DataFrame, key_prefix: str = "recent_claims") -> None:
    if df.empty:
        st.info("No claims found for this filter context.")
        return

    show_df = df.copy()
    show_df = show_df[[c for c in ENTERPRISE_COLUMNS if c in show_df.columns]]

    show_df = _sort_recent_claims(show_df, "DATE_REQUESTED", False)

    with st.container(key=f"{key_prefix}_recent_claims_table"):
        with st.container(key=f"{key_prefix}_recent_sort_header"):
            header_cols = st.columns(RECENT_CLAIMS_COLUMN_WIDTHS, vertical_alignment="center")
            header_labels = [
                "CLAIM ID",
                "PATIENT / DEFENDANT",
                "STATUS",
                "PRIORITY",
                "REQUESTED",
                "AI CONF.",
                "ACTIONS",
            ]

            for idx, label in enumerate(header_labels):
                header_cols[idx].markdown(
                    f"<div class='enterprise-header-cell'>{label}</div>",
                    unsafe_allow_html=True,
                )

        for _, row in show_df.iterrows():
            claim_id = str(row.get("CLAIM_ID", "")).strip()
            status = str(row.get("STATUS", "")).strip()
            patient_name = str(row.get("PATIENT_NAME", "")).strip() or "Unknown Patient"
            defendant_name = str(row.get("DEFENDANT_NAME", "")).strip()

            with st.container(key=f"{key_prefix}_recent_row_{claim_id}"):
                grid = st.columns(RECENT_CLAIMS_COLUMN_WIDTHS, vertical_alignment="center")
                grid[0].markdown(
                    f"<div class='enterprise-cell claim-id'><span class='cell-label'>Claim ID</span><span class='cell-value'>{escape(claim_id or '—')}</span></div>",
                    unsafe_allow_html=True,
                )

                person_detail = [f"<div class='patient-name'>{escape(patient_name)}</div>"]
                if defendant_name:
                    person_detail.append(f"<div class='defendant-name'>{escape(defendant_name)}</div>")

                grid[1].markdown(
                    f"<div class='enterprise-cell patient-cell'><span class='cell-label'>Patient / Defendant</span><span class='cell-value'>{''.join(person_detail)}</span></div>",
                    unsafe_allow_html=True,
                )
                grid[2].markdown(
                    f"<div class='enterprise-cell center-cell'><span class='cell-label'>Status</span><span class='cell-value'>{_status_badge_html(status)}</span></div>",
                    unsafe_allow_html=True,
                )
                grid[3].markdown(
                    f"<div class='enterprise-cell center-cell'><span class='cell-label'>Priority</span><span class='cell-value'>{_priority_badge_html(row.get('PRIORITY'))}</span></div>",
                    unsafe_allow_html=True,
                )
                grid[4].markdown(
                    f"<div class='enterprise-cell date-requested'><span class='cell-label'>Date Requested</span><span class='cell-value'>{escape(_format_date(row.get('DATE_REQUESTED')))}</span></div>",
                    unsafe_allow_html=True,
                )
                grid[5].markdown(
                    f"<div class='enterprise-cell center-cell'><span class='cell-label'>AI Confidence</span><span class='cell-value'>{_confidence_badge_html(row.get('AI_CONFIDENCE'))}</span></div>",
                    unsafe_allow_html=True,
                )

                action_slot = grid[6]
                with action_slot:
                    st.markdown("<div class='actions-cell'><div class='action-stack'>", unsafe_allow_html=True)
                    show_regenerate = status == "MFQ Generated"
                    pending_key = f"{key_prefix}_pending_confirm_{claim_id}"
                    running_key = f"{key_prefix}_running_{claim_id}"

                    if show_regenerate:
                        regen_clicked = st.button(
                            "↻ Regenerate",
                            key=f"{key_prefix}_regenerate_{claim_id}",
                            help="Regenerate MFQ using the latest claim documents and extracted data.",
                            disabled=bool(st.session_state.get(running_key, False)),
                            type="secondary",
                            use_container_width=True,
                        )
                        if regen_clicked:
                            st.session_state[pending_key] = True

                    review_pressed = st.button(
                        "Review →",
                        key=f"{key_prefix}_review_{claim_id}",
                        type="tertiary",
                        use_container_width=True,
                    )
                    if review_pressed:
                        st.session_state.selected_claim_id = claim_id
                        st.session_state.active_page = "Claim Details"
                        st.rerun()

                    if show_regenerate and st.session_state.get(pending_key, False):
                        st.markdown(
                            "<div class='regenerate-confirm'>Regenerating MFQ will replace the existing generated questionnaire for this claim. Do you want to continue?</div>",
                            unsafe_allow_html=True,
                        )
                        confirm_cols = st.columns([1, 1], vertical_alignment="center")
                        if confirm_cols[0].button(
                            "Cancel",
                            key=f"{key_prefix}_cancel_{claim_id}",
                            type="tertiary",
                            use_container_width=True,
                        ):
                            st.session_state[pending_key] = False
                            st.rerun()

                        if confirm_cols[1].button(
                            "Regenerate",
                            key=f"{key_prefix}_confirm_{claim_id}",
                            disabled=bool(st.session_state.get(running_key, False)),
                            type="primary",
                            use_container_width=True,
                        ):
                            st.session_state[running_key] = True
                            with st.spinner("Regenerating MFQ..."):
                                success, message = _run_regeneration(claim_id, row)
                            st.session_state[running_key] = False
                            st.session_state[pending_key] = False
                            if success:
                                st.success(message)
                                st.rerun()
                            st.error(message)
                    st.markdown("</div>", unsafe_allow_html=True)
            
