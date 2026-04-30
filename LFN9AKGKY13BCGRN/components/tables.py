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
RECENT_CLAIMS_COLUMN_WIDTHS = [12, 24, 12, 9, 13, 10, 20]

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

    rows_html: list[str] = []
    for _, row in show_df.iterrows():
        claim_id = str(row.get("CLAIM_ID", "")).strip() or "—"
        status = str(row.get("STATUS", "")).strip()
        patient_name = str(row.get("PATIENT_NAME", "")).strip() or "Unknown Patient"
        defendant_name = str(row.get("DEFENDANT_NAME", "")).strip()
        requested = _format_date(row.get("DATE_REQUESTED"))

        patient_html = f"<span class='patient-name'>{escape(patient_name)}</span>"
        if defendant_name:
            patient_html += f"<span class='defendant-name'>{escape(defendant_name)}</span>"

        actions_html = "<div class='action-stack'>"
        if status == "MFQ Generated":
            actions_html += "<span class='btn-regenerate'>↻ Regenerate</span>"
        actions_html += "<span class='btn-review'>Review →</span></div>"

        rows_html.append(
            "<tr>"
            f"<td class='claim-id-cell' data-label='Claim ID'>{escape(claim_id)}</td>"
            f"<td class='patient-cell' data-label='Patient / Defendant'>{patient_html}</td>"
            f"<td class='status-cell' data-label='Status'>{_status_badge_html(status)}</td>"
            f"<td class='priority-cell' data-label='Priority'>{_priority_badge_html(row.get('PRIORITY'))}</td>"
            f"<td class='requested-cell' data-label='Requested'>{escape(requested)}</td>"
            f"<td class='confidence-cell' data-label='AI Conf.'>{_confidence_badge_html(row.get('AI_CONFIDENCE'))}</td>"
            f"<td class='actions-cell' data-label='Actions'>{actions_html}</td>"
            "</tr>"
        )

    table_html = (
        "<div class='claims-table-scroll'>"
        "<table class='claims-table'>"
        "<colgroup>"
        "<col class='col-claim-id' />"
        "<col class='col-patient' />"
        "<col class='col-status' />"
        "<col class='col-priority' />"
        "<col class='col-requested' />"
        "<col class='col-confidence' />"
        "<col class='col-actions' />"
        "</colgroup>"
        "<thead><tr>"
        "<th>Claim ID</th>"
        "<th>Patient / Defendant</th>"
        "<th>Status</th>"
        "<th>Priority</th>"
        "<th>Requested</th>"
        "<th>AI Conf.</th>"
        "<th>Actions</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        "</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)
