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
    "MFQ_STATUS",
    "WORKFLOW_STATUS",
    "PRIORITY",
    "CLAIM_STATUS",
    "CLAIM_TYPE",
    "DATE_REQUESTED",
    "AI_CONFIDENCE",
    "STATUS",
]
RECENT_CLAIMS_HEADERS = [
    "Claim ID",
    "Patient / Defendant",
    "MFQ Status",
    "Workflow Status",
    "Priority",
    "Claim Status",
    "Claim Type",
    "Date Requested",
    "AI Conf.",
    "Actions",
]

RECENT_CLAIMS_COLUMN_WIDTHS = [110, 260, 170, 180, 120, 180, 140, 150, 120, 130]
RECENT_CLAIMS_SORT_COLUMNS = [
    ("CLAIM_ID", "Claim ID"),
    ("PATIENT_NAME", "Patient / Defendant"),
    ("MFQ_STATUS", "MFQ Status"),
    ("WORKFLOW_STATUS", "Workflow Status"),
    ("PRIORITY", "Priority"),
    ("DATE_REQUESTED", "Date Requested"),
    ("AI_CONFIDENCE", "AI Confidence"),
    ("CLAIM_TYPE", "Claim Type"),
    ("CLAIM_STATUS", "Claim Status"),
]
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2, "unknown": 3}

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


def _display_status_label(status: Any) -> str:
    label = str(status or "Unknown").strip()
    if not label:
        return "Unknown"
    if "_" in label:
        return label.replace("_", " ").title()
    return label


def _status_badge_html(status: Any) -> str:
    raw_label = str(status or "Unknown").strip() or "Unknown"
    label = _display_status_label(raw_label)
    tone = _normalize_slug(raw_label)
    return f"<span class='status-badge status-{tone}' title='{escape(raw_label)}'>{escape(label)}</span>"


def _priority_badge_html(priority: Any) -> str:
    raw_label = str(priority or "Unknown").strip() or "Unknown"
    label = _display_status_label(raw_label)
    tone = _normalize_slug(raw_label)
    return f"<span class='priority-badge priority-{tone}' title='{escape(raw_label)}'>{escape(label)}</span>"


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


def _toggle_sort_direction(current_column: str, selected_column: str, current_direction: str) -> str:
    if current_column != selected_column:
        return "asc"
    return "desc" if current_direction == "asc" else "asc"


def _claim_id_sort_series(series: pd.Series) -> pd.Series:
    as_text = series.fillna("").astype(str).str.strip()
    numeric = pd.to_numeric(as_text, errors="coerce")
    numeric_order = numeric.fillna(float("inf"))
    text_order = as_text.str.lower()
    return pd.DataFrame({"numeric_order": numeric_order, "text_order": text_order})


def _confidence_sort_series(series: pd.Series) -> pd.Series:
    cleaned = series.fillna("").astype(str).str.replace("%", "", regex=False).str.strip()
    numeric = pd.to_numeric(cleaned, errors="coerce")
    numeric = numeric.where((numeric > 1) | numeric.isna(), numeric * 100)
    return numeric.fillna(-1)


def _priority_sort_series(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    return normalized.map(PRIORITY_ORDER).fillna(PRIORITY_ORDER["unknown"])


def _recent_claim_sort_series(df: pd.DataFrame, sort_column: str) -> pd.Series | pd.DataFrame:
    if sort_column == "CLAIM_ID":
        return _claim_id_sort_series(df.get("CLAIM_ID", pd.Series(index=df.index, dtype="object")))
    if sort_column == "PATIENT_NAME":
        patient = df.get("PATIENT_NAME", pd.Series(index=df.index, dtype="object")).fillna("").astype(str)
        defendant = df.get("DEFENDANT_NAME", pd.Series(index=df.index, dtype="object")).fillna("").astype(str)
        return (patient + " " + defendant).str.lower().str.strip()
    if sort_column in {"MFQ_STATUS", "WORKFLOW_STATUS", "CLAIM_TYPE", "CLAIM_STATUS"}:
        return df.get(sort_column, pd.Series(index=df.index, dtype="object")).fillna("").astype(str).str.lower()
    if sort_column == "PRIORITY":
        return _priority_sort_series(df.get("PRIORITY", pd.Series(index=df.index, dtype="object")))
    if sort_column == "DATE_REQUESTED":
        return pd.to_datetime(df.get("DATE_REQUESTED", pd.Series(index=df.index, dtype="object")), errors="coerce")
    if sort_column == "AI_CONFIDENCE":
        return _confidence_sort_series(df.get("AI_CONFIDENCE", pd.Series(index=df.index, dtype="object")))
    return pd.Series(index=df.index, dtype="object")


def _sort_recent_claims(df: pd.DataFrame, sort_column: str | None, sort_direction: str) -> pd.DataFrame:
    if not sort_column:
        return df

    ascending = sort_direction == "asc"
    sort_value = _recent_claim_sort_series(df, sort_column)
    claim_ids = df.get("CLAIM_ID", pd.Series(index=df.index, dtype="object")).fillna("").astype(str)

    if isinstance(sort_value, pd.DataFrame):
        sortable = df.assign(
            _sort_key_numeric=sort_value["numeric_order"],
            _sort_key_text=sort_value["text_order"],
            _claim_id_tiebreaker=claim_ids,
        )
        return sortable.sort_values(
            by=["_sort_key_numeric", "_sort_key_text", "_claim_id_tiebreaker"],
            ascending=[ascending, ascending, True],
            na_position="first",
        ).drop(columns=["_sort_key_numeric", "_sort_key_text", "_claim_id_tiebreaker"], errors="ignore")

    return (
        df.assign(_sort_key=sort_value, _claim_id_tiebreaker=claim_ids)
        .sort_values(by=["_sort_key", "_claim_id_tiebreaker"], ascending=[ascending, True], na_position="first")
        .drop(columns=["_sort_key", "_claim_id_tiebreaker"], errors="ignore")
    )


def filter_recent_claims_by_search(df: pd.DataFrame, search_text: str) -> pd.DataFrame:
    needle = str(search_text or "").strip().lower()
    if not needle:
        return df
    search_columns = ["CLAIM_ID", "PATIENT_NAME", "DEFENDANT_NAME", "STATUS", "PRIORITY", "FILE_NUMBER"]
    mask = pd.Series(False, index=df.index)
    for column in search_columns:
        if column in df.columns:
            mask = mask | df[column].astype(str).str.lower().str.contains(needle)
    return df[mask]


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


def render_recent_claims_table(
    df: pd.DataFrame, key_prefix: str = "recent_claims", *, empty_message: str = "No claims found for this filter context."
) -> None:
    if df.empty:
        st.info(empty_message)
        return

    sort_key_base = f"{key_prefix}_recent_claims_sort"
    if f"{sort_key_base}_column" not in st.session_state:
        st.session_state[f"{sort_key_base}_column"] = None
    if f"{sort_key_base}_direction" not in st.session_state:
        st.session_state[f"{sort_key_base}_direction"] = "asc"
    pagination_key_base = f"{key_prefix}_recent_claims_pagination"
    page_size = 10
    if f"{pagination_key_base}_page" not in st.session_state:
        st.session_state[f"{pagination_key_base}_page"] = 1

    show_df = df.copy()
    show_df = show_df[[c for c in ENTERPRISE_COLUMNS if c in show_df.columns]]
    total_claims = len(show_df)
    total_pages = max(1, (total_claims + page_size - 1) // page_size)
    current_page = int(st.session_state.get(f"{pagination_key_base}_page", 1))
    current_page = max(1, min(current_page, total_pages))
    st.session_state[f"{pagination_key_base}_page"] = current_page
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_claims)
    page_df = show_df.iloc[start_idx:end_idx].copy()

    sort_column = st.session_state.get(f"{sort_key_base}_column")
    sort_direction = st.session_state.get(f"{sort_key_base}_direction", "asc")
    show_df = _sort_recent_claims(page_df, sort_column=sort_column, sort_direction=sort_direction)

    with st.container(key=f"{key_prefix}_recent_claims_table"):
        sort_headers = {label: key for key, label in RECENT_CLAIMS_SORT_COLUMNS}
        sort_bar_cols = st.columns(10, vertical_alignment="center")
        for idx, header in enumerate(RECENT_CLAIMS_HEADERS):
            with sort_bar_cols[idx]:
                if header in sort_headers:
                    selected_column = sort_headers[header]
                    is_active = sort_column == selected_column
                    arrow = "↑" if is_active and sort_direction == "asc" else "↓" if is_active else ""
                    header_label = f"{header} {arrow}" if arrow else header
                    if st.button(header_label, key=f"{sort_key_base}_header_{selected_column}", type="tertiary", use_container_width=True):
                        st.session_state[f"{sort_key_base}_direction"] = _toggle_sort_direction(
                            current_column=sort_column or "",
                            selected_column=selected_column,
                            current_direction=sort_direction,
                        )
                        st.session_state[f"{sort_key_base}_column"] = selected_column
                        st.rerun()
                else:
                    st.markdown(f"<div class='recent-claims-col-header'>{escape(header)}</div>", unsafe_allow_html=True)

        rows_html: list[str] = []
        for _, row in show_df.iterrows():
            claim_id = str(row.get("CLAIM_ID", "")).strip() or "—"
            status = str(row.get("STATUS", "")).strip()
            patient_name = str(row.get("PATIENT_NAME", "")).strip() or "Unknown Patient"
            defendant_name = str(row.get("DEFENDANT_NAME", "")).strip()
            requested = _format_date(row.get("DATE_REQUESTED"))

            patient_title = patient_name if not defendant_name else f"{patient_name} — {defendant_name}"
            patient_html = f"<span class='patient-name' title='{escape(patient_title)}'>{escape(patient_name)}</span>"
            if defendant_name:
                patient_html += f"<span class='defendant-name' title='{escape(patient_title)}'>{escape(defendant_name)}</span>"

            mfq_status = str(row.get("MFQ_STATUS", row.get("STATUS", ""))).strip()
            workflow_status = str(row.get("WORKFLOW_STATUS", row.get("STATUS", ""))).strip()
            claim_status = str(row.get("CLAIM_STATUS", row.get("STATUS", ""))).strip()
            claim_type = str(row.get("CLAIM_TYPE", "—")).strip() or "—"
            display_claim_type = _display_status_label(claim_type)
            rows_html.append(
                "<tr>"
                f"<td class='recent-claims-td' style='width:110px'><div class='single-line-ellipsis' title='{escape(claim_id)}'>{escape(claim_id)}</div></td>"
                f"<td class='recent-claims-td' style='width:280px'><div class='patient-cell'>{patient_html}</div></td>"
                f"<td class='recent-claims-td' style='width:180px'><div class='status-cell'>{_status_badge_html(mfq_status)}</div></td>"
                f"<td class='recent-claims-td' style='width:200px'><div class='status-cell'>{_status_badge_html(workflow_status)}</div></td>"
                f"<td class='recent-claims-td' style='width:130px'><div class='priority-cell'>{_priority_badge_html(row.get('PRIORITY'))}</div></td>"
                f"<td class='recent-claims-td' style='width:200px'><div class='status-cell'>{_status_badge_html(claim_status)}</div></td>"
                f"<td class='recent-claims-td' style='width:150px'><div class='single-line-ellipsis' title='{escape(claim_type)}'>{escape(display_claim_type)}</div></td>"
                f"<td class='recent-claims-td' style='width:160px'><div class='single-line-ellipsis' title='{escape(requested)}'>{escape(requested)}</div></td>"
                f"<td class='recent-claims-td' style='width:130px'><div class='confidence-cell'>{_confidence_badge_html(row.get('AI_CONFIDENCE'))}</div></td>"
                "<td class='recent-claims-td sticky-actions' style='width:130px'><div class='actions-slot'>Actions</div></td>"
                "</tr>"
            )
        st.markdown(
            "<div class='recent-claims-table-wrapper'><table class='recent-claims-table'><tbody>"
            + "".join(rows_html)
            + "</tbody></table></div>",
            unsafe_allow_html=True,
        )

        for _, row in show_df.iterrows():
            claim_id = str(row.get("CLAIM_ID", "")).strip() or "—"
            status = str(row.get("STATUS", "")).strip()
            with st.container():
                review_key = f"{key_prefix}_review_{claim_id}"
                has_regen = status == "MFQ Generated"
                action_cell_class = "actions-cell actions-cell-stacked" if has_regen else "actions-cell actions-cell-single"
                st.markdown(f"<div class='{action_cell_class}'>", unsafe_allow_html=True)
                if st.button("Review", key=review_key, type="secondary"):
                    st.session_state["selected_claim_id"] = claim_id
                    st.session_state["current_view"] = "claim_details"
                    st.session_state["active_page"] = "Dashboard"
                    st.rerun()

                if has_regen:
                    regen_key = f"{key_prefix}_regenerate_{claim_id}"
                    if st.button("Regenerate", key=regen_key, type="secondary"):
                        ok, message = _run_regeneration(claim_id=claim_id, row=row)
                        if ok:
                            st.success(message)
                        else:
                            st.error(message)
                st.markdown("</div>", unsafe_allow_html=True)
        summary_text = f"Showing {start_idx + 1}-{end_idx} of {total_claims} claims"
        pager_cols = st.columns([3, 1], vertical_alignment="center")
        pager_cols[0].markdown(f"<div class='recent-claims-pagination-summary'>{summary_text}</div>", unsafe_allow_html=True)
        with pager_cols[1]:
            prev_col, next_col = st.columns(2)
            with prev_col:
                if st.button("Previous", key=f"{pagination_key_base}_prev", disabled=current_page <= 1, use_container_width=True):
                    st.session_state[f"{pagination_key_base}_page"] = max(1, current_page - 1)
                    st.rerun()
            with next_col:
                if st.button("Next", key=f"{pagination_key_base}_next", disabled=current_page >= total_pages, use_container_width=True):
                    st.session_state[f"{pagination_key_base}_page"] = min(total_pages, current_page + 1)
                    st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)
