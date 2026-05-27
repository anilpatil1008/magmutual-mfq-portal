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
RECENT_CLAIMS_COLUMNS = [
    {"key": "CLAIM_ID", "label": "Claim ID", "width": 110, "sortable": True},
    {"key": "PATIENT_NAME", "label": "Patient / Defendant", "width": 280, "sortable": True},
    {"key": "MFQ_STATUS", "label": "MFQ Status", "width": 180, "sortable": True},
    {"key": "WORKFLOW_STATUS", "label": "Workflow Status", "width": 200, "sortable": True},
    {"key": "PRIORITY", "label": "Priority", "width": 130, "sortable": True},
    {"key": "CLAIM_STATUS", "label": "Claim Status", "width": 200, "sortable": True},
    {"key": "CLAIM_TYPE", "label": "Claim Type", "width": 150, "sortable": True},
    {"key": "DATE_REQUESTED", "label": "Date Requested", "width": 160, "sortable": True},
    {"key": "AI_CONFIDENCE", "label": "AI Conf.", "width": 130, "sortable": True},
    {"key": "ACTIONS", "label": "Actions", "width": 130, "sortable": False},
]

RECENT_CLAIMS_WIDTH_MAP = {c["key"]: c["width"] for c in RECENT_CLAIMS_COLUMNS}
RECENT_CLAIMS_SORTABLE_KEYS = {c["key"] for c in RECENT_CLAIMS_COLUMNS if c["sortable"]}
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

    pagination_key_base = f"{key_prefix}_recent_claims_pagination"
    page_size = 10
    if f"{pagination_key_base}_page" not in st.session_state:
        st.session_state[f"{pagination_key_base}_page"] = 1

    show_df = df.copy()
    show_df = show_df[[c for c in ENTERPRISE_COLUMNS if c in show_df.columns]]

    sort_key_base = f"{key_prefix}_recent_claims_sort"
    sort_column_key = f"{sort_key_base}_column"
    sort_direction_key = f"{sort_key_base}_direction"
    if sort_column_key not in st.session_state:
        st.session_state[sort_column_key] = None
    if sort_direction_key not in st.session_state:
        st.session_state[sort_direction_key] = "asc"

    sort_column = st.session_state.get(sort_column_key)
    sort_direction = st.session_state.get(sort_direction_key, "asc")
    show_df = _sort_recent_claims(show_df, sort_column, sort_direction)

    total_claims = len(show_df)
    total_pages = max(1, (total_claims + page_size - 1) // page_size)
    current_page = int(st.session_state.get(f"{pagination_key_base}_page", 1))
    current_page = max(1, min(current_page, total_pages))
    st.session_state[f"{pagination_key_base}_page"] = current_page
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_claims)
    page_df = show_df.iloc[start_idx:end_idx].copy()

    show_df = page_df

    with st.container(key=f"{key_prefix}_recent_claims_table"):
        column_widths = [c["width"] for c in RECENT_CLAIMS_COLUMNS]
        total_width = float(sum(column_widths))
        normalized_widths = [w / total_width for w in column_widths]

        header_cols = st.columns(normalized_widths, vertical_alignment="center")
        for idx, column in enumerate(RECENT_CLAIMS_COLUMNS):
            col_key = column["key"]
            label = column["label"]
            with header_cols[idx]:
                if column["sortable"]:
                    arrow = ""
                    if sort_column == col_key:
                        arrow = " ↑" if sort_direction == "asc" else " ↓"
                    if st.button(
                        f"{label}{arrow}",
                        key=f"{sort_key_base}_{col_key}_header_button",
                        use_container_width=True,
                    ):
                        current_column = st.session_state.get(sort_column_key)
                        current_direction = st.session_state.get(sort_direction_key, "asc")
                        st.session_state[sort_column_key] = col_key
                        st.session_state[sort_direction_key] = _toggle_sort_direction(
                            current_column=current_column,
                            selected_column=col_key,
                            current_direction=current_direction,
                        )
                        st.rerun()
                else:
                    st.markdown(f"**{label}**")

        st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)

        for _, row in show_df.iterrows():
            claim_id = str(row.get("CLAIM_ID", "")).strip() or "—"
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
            row_cols = st.columns(normalized_widths, vertical_alignment="center")
            row_cols[0].markdown(
                f"<div class='single-line-ellipsis' title='{escape(claim_id)}'>{escape(claim_id)}</div>",
                unsafe_allow_html=True,
            )
            row_cols[1].markdown(f"<div class='patient-cell'>{patient_html}</div>", unsafe_allow_html=True)
            row_cols[2].markdown(f"<div class='status-cell'>{_status_badge_html(mfq_status)}</div>", unsafe_allow_html=True)
            row_cols[3].markdown(
                f"<div class='status-cell'>{_status_badge_html(workflow_status)}</div>",
                unsafe_allow_html=True,
            )
            row_cols[4].markdown(
                f"<div class='priority-cell'>{_priority_badge_html(row.get('PRIORITY'))}</div>",
                unsafe_allow_html=True,
            )
            row_cols[5].markdown(
                f"<div class='status-cell'>{_status_badge_html(claim_status)}</div>",
                unsafe_allow_html=True,
            )
            row_cols[6].markdown(
                f"<div class='single-line-ellipsis' title='{escape(claim_type)}'>{escape(display_claim_type)}</div>",
                unsafe_allow_html=True,
            )
            row_cols[7].markdown(
                f"<div class='single-line-ellipsis' title='{escape(requested)}'>{escape(requested)}</div>",
                unsafe_allow_html=True,
            )
            row_cols[8].markdown(
                f"<div class='confidence-cell'>{_confidence_badge_html(row.get('AI_CONFIDENCE'))}</div>",
                unsafe_allow_html=True,
            )
            with row_cols[9]:
                if st.button("Review", key=f"{key_prefix}_review_{claim_id}", use_container_width=True):
                    st.session_state.selected_claim_id = claim_id
                    st.session_state.active_page = "Claim Details"
                    st.rerun()
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
