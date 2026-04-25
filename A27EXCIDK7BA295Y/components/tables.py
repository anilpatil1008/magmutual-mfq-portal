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
    "SPECIALTY",
    "STATUS",
    "PRIORITY",
    "DATE_REQUESTED",
    "AI_CONFIDENCE",
]


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
        if st.button(f"Open {claim_id}", key=btn_key):
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

    header_html = """
    <div class='enterprise-table'>
      <table>
        <thead>
          <tr>
            <th>Claim ID</th>
            <th>Patient / Defendant</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Date Requested</th>
            <th>AI Confidence</th>
            <th>Action</th>
          </tr>
        </thead>
      </table>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    for _, row in show_df.iterrows():
        claim_id = str(row.get("CLAIM_ID", "")).strip()
        status = str(row.get("STATUS", "")).strip()
        patient_name = str(row.get("PATIENT_NAME", "")).strip() or "Unknown Patient"
        defendant_name = str(row.get("DEFENDANT_NAME", "")).strip()
        specialty = str(row.get("SPECIALTY", "")).strip()

        grid = st.columns([1.05, 2.3, 1.15, 1.0, 1.2, 1.05, 1.45], vertical_alignment="center")

        grid[0].markdown(f"<div class='enterprise-cell claim-id'>{escape(claim_id or '—')}</div>", unsafe_allow_html=True)

        person_detail = [f"<div class='patient-name'>{escape(patient_name)}</div>"]
        if defendant_name:
            person_detail.append(f"<div class='defendant-name'>{escape(defendant_name)}</div>")
        if specialty and specialty.lower() not in {"nan", "none"}:
            person_detail.append(f"<div class='specialty-name'>{escape(specialty)}</div>")

        grid[1].markdown(
            f"<div class='enterprise-cell patient-cell'>{''.join(person_detail)}</div>",
            unsafe_allow_html=True,
        )
        grid[2].markdown(f"<div class='enterprise-cell'>{_status_badge_html(status)}</div>", unsafe_allow_html=True)
        grid[3].markdown(
            f"<div class='enterprise-cell'>{_priority_badge_html(row.get('PRIORITY'))}</div>",
            unsafe_allow_html=True,
        )
        grid[4].markdown(
            f"<div class='enterprise-cell date-requested'>{escape(_format_date(row.get('DATE_REQUESTED')))}</div>",
            unsafe_allow_html=True,
        )
        grid[5].markdown(
            f"<div class='enterprise-cell'>{_confidence_badge_html(row.get('AI_CONFIDENCE'))}</div>",
            unsafe_allow_html=True,
        )

        action_slot = grid[6]
        with action_slot:
            action_cols = st.columns([1.1, 1.0], vertical_alignment="center")

            show_regenerate = status == "MFQ Generated"
            regen_clicked = False
            if show_regenerate:
                regen_key = f"{key_prefix}_regenerate_{claim_id}"
                pending_key = f"{key_prefix}_pending_confirm_{claim_id}"
                running_key = f"{key_prefix}_running_{claim_id}"

                regen_clicked = action_cols[0].button(
                    "↻ Regenerate",
                    key=regen_key,
                    help="Regenerate MFQ using the latest claim documents and extracted data.",
                    disabled=bool(st.session_state.get(running_key, False)),
                    use_container_width=True,
                )
                if regen_clicked:
                    st.session_state[pending_key] = True

            review_key = f"{key_prefix}_review_{claim_id}"
            if action_cols[1].button("Review →", key=review_key, use_container_width=True):
                st.session_state.selected_claim_id = claim_id
                st.session_state.active_page = "Claim Details"
                st.rerun()

            if show_regenerate:
                pending_key = f"{key_prefix}_pending_confirm_{claim_id}"
                running_key = f"{key_prefix}_running_{claim_id}"
                if st.session_state.get(pending_key, False):
                    st.markdown(
                        "<div class='regenerate-confirm'>Regenerating MFQ will replace the existing generated questionnaire for this claim. Do you want to continue?</div>",
                        unsafe_allow_html=True,
                    )
                    confirm_cols = st.columns([1, 1], vertical_alignment="center")
                    if confirm_cols[0].button("Cancel", key=f"{key_prefix}_cancel_{claim_id}", use_container_width=True):
                        st.session_state[pending_key] = False
                        st.rerun()

                    if confirm_cols[1].button(
                        "Regenerate",
                        key=f"{key_prefix}_confirm_{claim_id}",
                        disabled=bool(st.session_state.get(running_key, False)),
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

        st.markdown("<div class='enterprise-row-separator'></div>", unsafe_allow_html=True)
