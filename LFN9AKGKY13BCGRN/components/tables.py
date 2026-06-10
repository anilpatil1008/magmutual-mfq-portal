from __future__ import annotations

from datetime import datetime
from time import perf_counter
import logging
from html import escape
from pathlib import Path
from typing import Any
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from components.badges import (
    PRIORITY_ORDER,
    normalize_badge_value,
    render_priority_badge,
    render_status_badge,
    safe_display,
    status_badge,
)
from utils.navigation import navigate_to_claim_details

logger = logging.getLogger(__name__)


_RECENT_CLAIMS_TABLE_COMPONENT = components.declare_component(
    "recent_claims_table",
    path=str(Path(__file__).resolve().parent / "recent_claims_table_component"),
)

_LIVE_SEARCH_INPUT_COMPONENT = components.declare_component(
    "live_search_input",
    path=str(Path(__file__).resolve().parent / "live_search_input_component"),
)


VISIBLE_COLUMNS = [
    "CLAIM_ID",
    "FILE_NUMBER",
    "PATIENT_DEFENDANT",
    "MFQ_STATUS",
    "WORKFLOW_STATUS",
    "PRIORITY",
    "CLAIM_STATUS",
    "CLAIM_TYPE",
    "DATE_REQUESTED",
    "AI_CONFIDENCE",
]

ENTERPRISE_COLUMNS = [
    "CLAIM_ID",
    "FILE_NUMBER",
    "PATIENT_DEFENDANT",
    "MFQ_STATUS",
    "WORKFLOW_STATUS",
    "PRIORITY",
    "CLAIM_STATUS",
    "CLAIM_TYPE",
    "DATE_REQUESTED",
    "AI_CONFIDENCE",
]
RECENT_CLAIMS_COLUMNS = [
    {"key": "CLAIM_ID", "label": "Claim ID", "width": 110, "sortable": True},
    {"key": "PATIENT_DEFENDANT", "label": "Patient / Defendant", "width": 280, "sortable": True},
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


def _normalize_claim_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize known Snowflake column names to the uppercase names used by renderers."""
    normalized = df.copy()
    case_map = {str(column).casefold(): column for column in normalized.columns}
    for target in set(VISIBLE_COLUMNS + ENTERPRISE_COLUMNS + ["CLAIM_PRIORITY", "STATUS"]):
        actual = case_map.get(target.casefold())
        if actual is not None and actual != target and target not in normalized.columns:
            normalized[target] = normalized[actual]
    if "PRIORITY" not in normalized.columns and "CLAIM_PRIORITY" in normalized.columns:
        normalized["PRIORITY"] = normalized["CLAIM_PRIORITY"]
    if "CLAIM_ID" not in normalized.columns and "FILE_NUMBER" in normalized.columns:
        normalized["CLAIM_ID"] = normalized["FILE_NUMBER"]
    return normalized


def _display_patient_defendant(value: Any) -> str:
    """Return the Snowflake PATIENT_DEFENDANT value unless it is null or blank."""
    return safe_display(value, fallback="Unknown Patient")


def _load_recent_claims_table_css() -> str:
    css_candidates = [
        Path(__file__).resolve().parent / "styles" / "carbonstyle.css",
        Path(__file__).resolve().parent / "styles" / "carbon_like.css",
        Path(__file__).resolve().parents[1] / "styles" / "carbonstyle.css",
        Path(__file__).resolve().parents[1] / "styles" / "carbon_like.css",
    ]

    for css_path in css_candidates:
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")

    return ""


def _top_scroll_sync_script(root_selector: str, wrapper_selector: str, table_selector: str) -> str:
    return f"""
    <script>
        (() => {{
            const root = document.querySelector('{root_selector}');
            if (!root || root.dataset.scrollSyncReady === 'true') return;
            root.dataset.scrollSyncReady = 'true';

            const topScrollbar = root.querySelector('.table-top-scrollbar');
            const topScrollbarSpacer = root.querySelector('.table-top-scrollbar-spacer');
            const wrapper = root.querySelector('{wrapper_selector}');
            const table = root.querySelector('{table_selector}');

            if (!topScrollbar || !topScrollbarSpacer || !wrapper || !table) return;

            let isSyncing = false;
            let resizeObserver;

            const syncSpacerWidth = () => {{
                topScrollbarSpacer.style.width = `${{table.scrollWidth}}px`;
                topScrollbar.style.width = `${{wrapper.clientWidth}}px`;
                topScrollbar.scrollLeft = wrapper.scrollLeft;
            }};

            const syncScrollLeft = (source, target) => {{
                if (isSyncing) return;
                isSyncing = true;
                target.scrollLeft = source.scrollLeft;
                window.requestAnimationFrame(() => {{
                    isSyncing = false;
                }});
            }};

            topScrollbar.addEventListener('scroll', () => syncScrollLeft(topScrollbar, wrapper));
            wrapper.addEventListener('scroll', () => syncScrollLeft(wrapper, topScrollbar));

            syncSpacerWidth();
            window.addEventListener('resize', syncSpacerWidth);

            if ('ResizeObserver' in window) {{
                resizeObserver = new ResizeObserver(syncSpacerWidth);
                resizeObserver.observe(wrapper);
                resizeObserver.observe(table);
            }}
        }})();
    </script>
    """


def _recent_claims_sort_script() -> str:
    return """
    <script>
        (() => {
            const wrapper = document.querySelector('.recent-claims-table-wrapper');
            if (!wrapper) return;

            const table = wrapper.querySelector('.recent-claims-table');
            const tbody = table?.querySelector('.recent-claims-tbody');
            const buttons = table?.querySelectorAll('.recent-claims-sort-button');

            if (!table || !tbody || !buttons || buttons.length === 0) return;

            const state = { key: null, direction: 'asc' };

            const parseValue = (value, type) => {
                if (type === 'number' || type === 'date' || type === 'priority') {
                    const parsed = Number(value);
                    return Number.isNaN(parsed) ? -1 : parsed;
                }
                return String(value || '').toLowerCase();
            };

            buttons.forEach((button, index) => {
                button.addEventListener('click', () => {
                    const key = button.dataset.sortKey;
                    const type = button.dataset.sortType || 'text';

                    state.direction =
                        state.key === key && state.direction === 'asc'
                            ? 'desc'
                            : 'asc';

                    state.key = key;

                    const rows = Array.from(tbody.querySelectorAll('tr'));

                    rows.sort((a, b) => {
                        const aValue = parseValue(a.children[index]?.dataset.sortValue, type);
                        const bValue = parseValue(b.children[index]?.dataset.sortValue, type);

                        if (aValue < bValue) return state.direction === 'asc' ? -1 : 1;
                        if (aValue > bValue) return state.direction === 'asc' ? 1 : -1;
                        return 0;
                    });

                    rows.forEach((row) => tbody.appendChild(row));

                    buttons.forEach((btn) => {
                        btn.classList.remove('active-sort', 'sort-asc', 'sort-desc');
                        const arrow = btn.querySelector('.sort-arrow');
                        if (arrow) arrow.textContent = '';
                    });

                    button.classList.add(
                        'active-sort',
                        state.direction === 'asc' ? 'sort-asc' : 'sort-desc'
                    );

                    const arrow = button.querySelector('.sort-arrow');
                    if (arrow) {
                        arrow.textContent = state.direction === 'asc' ? '↑' : '↓';
                    }
                });
            });
        })();
    </script>
    """


def _normalize_slug(value: Any) -> str:
    text = normalize_badge_value(value).replace(" ", "-")
    return "".join(ch for ch in text if ch.isalnum() or ch == "-") or "default"


def _format_date(value: Any) -> str:
    if safe_display(value, fallback="") == "":
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime("%b %d, %Y")
    as_text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(as_text[:19], fmt).strftime("%b %d, %Y")
        except ValueError:
            continue
    return as_text


def _display_status_label(status: Any) -> str:
    label = safe_display(status)
    if label == "-":
        return "-"
    if "_" in label:
        return label.replace("_", " ").title()
    return label


def _status_badge_html(status: Any) -> str:
    return render_status_badge(status)


def _priority_badge_html(priority: Any) -> str:
    return render_priority_badge(priority)


def _confidence_badge_html(confidence: Any) -> str:
    if safe_display(confidence, fallback="") == "":
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
    normalized = series.apply(normalize_badge_value)
    return normalized.map(PRIORITY_ORDER).fillna(PRIORITY_ORDER["unknown"])


def _recent_claim_sort_series(df: pd.DataFrame, sort_column: str) -> pd.Series | pd.DataFrame:
    if sort_column == "CLAIM_ID":
        return _claim_id_sort_series(df.get("CLAIM_ID", pd.Series(index=df.index, dtype="object")))
    if sort_column == "PATIENT_DEFENDANT":
        return df.get("PATIENT_DEFENDANT", pd.Series(index=df.index, dtype="object")).fillna("").astype(str).str.lower()
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


def render_live_claims_search(
    *,
    value: str,
    table_key: str,
    placeholder: str = "Search by patient, defendant, claim ID, file #, or status...",
    height: int = 48,
    debounce_ms: int = 275,
) -> str | None:
    """Render a Carbon-like search input that emits on every browser input event."""
    event = _LIVE_SEARCH_INPUT_COMPONENT(
        value=str(value or ""),
        placeholder=placeholder,
        aria_label=placeholder,
        table_key=table_key,
        height=height,
        debounce_ms=debounce_ms,
        key=f"{table_key}_live_search_input_component",
        default=None,
    )
    if isinstance(event, dict):
        return str(event.get("search_text") or "")
    return None


def filter_recent_claims_by_search(df: pd.DataFrame, search_text: str) -> pd.DataFrame:
    needle = str(search_text or "").strip().lower()
    if not needle:
        return df
    search_columns = [
        "CLAIM_ID",
        "FILE_NUMBER",
        "PATIENT_DEFENDANT",
        "DEFENDANT_NAME",
        "MFQ_STATUS",
        "WORKFLOW_STATUS",
        "PRIORITY",
        "CLAIM_STATUS",
        "CLAIM_TYPE",
    ]
    mask = pd.Series(False, index=df.index)
    for column in search_columns:
        if column in df.columns:
            mask = mask | df[column].astype(str).str.lower().str.contains(needle)
    return df[mask]


def _open_claim_details(claim_id: str) -> None:
    started = perf_counter()
    claim_id = str(claim_id).strip()
    st.session_state["review_click_started_at"] = started
    st.session_state["last_review_event"] = None
    st.session_state["last_processed_review_claim_id"] = claim_id
    logger.info("review_click_state_update_ms=%d claim_id=%s", int((perf_counter() - started) * 1000), claim_id)
    navigate_to_claim_details(claim_id)


def render_claims_table(df: pd.DataFrame, key_prefix: str = "claims") -> None:
    if df.empty:
        st.info("No claims found for this filter context.")
        return

    show_df = _normalize_claim_columns(df)
    show_df = show_df[[c for c in VISIBLE_COLUMNS if c in show_df.columns]]

    if "PATIENT_DEFENDANT" not in show_df.columns:
        show_df["PATIENT_DEFENDANT"] = "Unknown Patient"
        show_df = show_df[[c for c in VISIBLE_COLUMNS if c in show_df.columns]]
    else:
        show_df["PATIENT_DEFENDANT"] = show_df["PATIENT_DEFENDANT"].apply(_display_patient_defendant)

    for status_column in ("MFQ_STATUS", "STATUS"):
        if status_column in show_df.columns:
            show_df[status_column] = show_df[status_column].apply(status_badge)
    if "PRIORITY" in show_df.columns:
        show_df["PRIORITY"] = show_df["PRIORITY"].apply(render_priority_badge)
    for text_column in show_df.columns:
        if text_column not in {"MFQ_STATUS", "STATUS", "PRIORITY"}:
            show_df[text_column] = show_df[text_column].apply(safe_display)

    rows = []
    for _, row in show_df.iterrows():
        claim_id = row.get("CLAIM_ID", "")
        btn_key = f"{key_prefix}_open_{claim_id}"
        if st.button(f"Review {claim_id}", key=btn_key):
            _open_claim_details(str(claim_id))

        row_html = "".join([f"<td>{value}</td>" for value in row.values])
        rows.append(f"<tr>{row_html}</tr>")

    head_html = "".join([f"<th>{h}</th>" for h in show_df.columns])
    claims_table_css = _load_recent_claims_table_css()
    table_html = (
        f"<style>{claims_table_css}</style>"
        "<div class='claims-table-scroll-frame'>"
        "<div class='table-top-scrollbar' aria-hidden='true'><div class='table-top-scrollbar-spacer'></div></div>"
        "<div class='claims-table-wrapper'>"
        f"<table class='mm-table claims-scroll-table'><thead><tr>{head_html}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
        "</div>"
        "</div>"
        + _top_scroll_sync_script('.claims-table-scroll-frame', '.claims-table-wrapper', '.claims-scroll-table')
    )
    components.html(table_html, height=560, scrolling=False)


def render_recent_claims_table(
    df: pd.DataFrame,
    key_prefix: str = "recent_claims",
    *,
    empty_message: str = "No claims found for this filter context.",
    total_claims: int | None = None,
    page: int | None = None,
    page_size: int = 10,
    pagination_state_key: str | None = None,
    table_key: str | None = None,
    component_key: str | None = None,
) -> None:
    stable_table_key = table_key or f"{key_prefix}_recent_claims_table"
    stable_component_key = component_key or f"{stable_table_key}_component"
    pagination_key_base = f"{key_prefix}_recent_claims_pagination"
    page_state_key = pagination_state_key or f"{pagination_key_base}_page"
    if page_state_key not in st.session_state:
        st.session_state[page_state_key] = 1

    if df.empty and not total_claims:
        st.info(empty_message)
        return

    show_df = _normalize_claim_columns(df)
    show_df = show_df[[c for c in ENTERPRISE_COLUMNS if c in show_df.columns]]
    if "PATIENT_DEFENDANT" not in show_df.columns:
        show_df["PATIENT_DEFENDANT"] = "Unknown Patient"
        show_df = show_df[[c for c in ENTERPRISE_COLUMNS if c in show_df.columns]]
    else:
        show_df["PATIENT_DEFENDANT"] = show_df["PATIENT_DEFENDANT"].apply(_display_patient_defendant)
    is_server_paginated = total_claims is not None or page is not None
    total_claims = int(total_claims if total_claims is not None else len(show_df))
    total_pages = max(1, (total_claims + page_size - 1) // page_size)
    current_page = int(page if page is not None else st.session_state.get(page_state_key, 1))
    current_page = max(1, min(current_page, total_pages))
    st.session_state[page_state_key] = current_page
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + len(show_df), total_claims) if is_server_paginated else min(start_idx + page_size, total_claims)
    if not is_server_paginated:
        show_df = show_df.iloc[start_idx:end_idx].copy()

    if show_df.empty:
        st.info(empty_message)
        return

    with st.container(key=f"{stable_table_key}_container"):
        header_cells: list[str] = []
        for column in RECENT_CLAIMS_COLUMNS:
            col_key = column["key"]
            label = column["label"]
            width_px = column["width"]
            th_classes = "recent-claims-th sticky-actions-header" if col_key == "ACTIONS" else "recent-claims-th"
            if column["sortable"]:
                sort_type = "text"
                if col_key in {"CLAIM_ID", "AI_CONFIDENCE"}:
                    sort_type = "number"
                elif col_key == "DATE_REQUESTED":
                    sort_type = "date"
                elif col_key == "PRIORITY":
                    sort_type = "priority"
                header_label = (
                    f"<button type='button' class='recent-claims-sort-button' data-sort-key='{escape(col_key)}' "
                    f"data-sort-type='{sort_type}'><span>{escape(label)}</span><span class='sort-arrow'></span></button>"
                )
            else:
                header_label = escape(label)
            header_cells.append(f"<th class='{th_classes}' style='width:{width_px}px'>{header_label}</th>")

        rows_html: list[str] = []
        for _, row in show_df.iterrows():
            claim_id = safe_display(row.get("CLAIM_ID"), fallback="—")
            patient_defendant = _display_patient_defendant(row.get("PATIENT_DEFENDANT"))
            requested = _format_date(row.get("DATE_REQUESTED"))
            requested_ts = pd.to_datetime(row.get("DATE_REQUESTED"), errors="coerce")
            requested_sort = str(int(requested_ts.timestamp())) if not pd.isna(requested_ts) else "-1"
            claim_id_sort_value = str(pd.to_numeric(str(claim_id), errors="coerce"))
            if claim_id_sort_value == "nan":
                claim_id_sort_value = "-1"
            patient_sort_value = patient_defendant.lower()
            mfq_sort_value = _display_status_label(str(row.get("MFQ_STATUS", "")).strip()).lower()
            workflow_sort_value = _display_status_label(str(row.get("WORKFLOW_STATUS", "")).strip()).lower()
            priority_sort_value = normalize_badge_value(row.get("PRIORITY"))
            priority_sort_rank = str(PRIORITY_ORDER.get(priority_sort_value, PRIORITY_ORDER["unknown"]))
            claim_status_sort_value = _display_status_label(str(row.get("CLAIM_STATUS", "")).strip()).lower()
            ai_confidence_sort = str(_confidence_sort_series(pd.Series([row.get("AI_CONFIDENCE")])).iloc[0])

            patient_title = patient_defendant
            patient_html = f"<span class='patient-name' title='{escape(patient_title)}'>{escape(patient_defendant)}</span>"

            mfq_status = safe_display(row.get("MFQ_STATUS"))
            workflow_status = safe_display(row.get("WORKFLOW_STATUS"))
            claim_status = safe_display(row.get("CLAIM_STATUS"))
            claim_type = safe_display(row.get("CLAIM_TYPE"), fallback="—")
            display_claim_type = _display_status_label(claim_type)
            rows_html.append(
                "<tr>"
                f"<td class='recent-claims-td' data-sort-value='{escape(claim_id_sort_value)}' style='width:{RECENT_CLAIMS_WIDTH_MAP['CLAIM_ID']}px'><div class='single-line-ellipsis' title='{escape(claim_id)}'>{escape(claim_id)}</div></td>"
                f"<td class='recent-claims-td' data-sort-value='{escape(patient_sort_value)}' style='width:{RECENT_CLAIMS_WIDTH_MAP['PATIENT_DEFENDANT']}px'><div class='patient-cell'>{patient_html}</div></td>"
                f"<td class='recent-claims-td' data-sort-value='{escape(mfq_sort_value)}' style='width:{RECENT_CLAIMS_WIDTH_MAP['MFQ_STATUS']}px'><div class='status-cell'>{_status_badge_html(mfq_status)}</div></td>"
                f"<td class='recent-claims-td' data-sort-value='{escape(workflow_sort_value)}' style='width:{RECENT_CLAIMS_WIDTH_MAP['WORKFLOW_STATUS']}px'><div class='status-cell'>{_status_badge_html(workflow_status)}</div></td>"
                f"<td class='recent-claims-td' data-sort-value='{escape(priority_sort_rank)}' style='width:{RECENT_CLAIMS_WIDTH_MAP['PRIORITY']}px'><div class='priority-cell'>{_priority_badge_html(row.get('PRIORITY'))}</div></td>"
                f"<td class='recent-claims-td' data-sort-value='{escape(claim_status_sort_value)}' style='width:{RECENT_CLAIMS_WIDTH_MAP['CLAIM_STATUS']}px'><div class='status-cell'>{_status_badge_html(claim_status)}</div></td>"
                f"<td class='recent-claims-td' data-sort-value='{escape(display_claim_type.lower())}' style='width:{RECENT_CLAIMS_WIDTH_MAP['CLAIM_TYPE']}px'><div class='single-line-ellipsis' title='{escape(claim_type)}'>{escape(display_claim_type)}</div></td>"
                f"<td class='recent-claims-td' data-sort-value='{escape(requested_sort)}' style='width:{RECENT_CLAIMS_WIDTH_MAP['DATE_REQUESTED']}px'><div class='single-line-ellipsis' title='{escape(requested)}'>{escape(requested)}</div></td>"
                f"<td class='recent-claims-td' data-sort-value='{escape(ai_confidence_sort)}' style='width:{RECENT_CLAIMS_WIDTH_MAP['AI_CONFIDENCE']}px'><div class='confidence-cell'>{_confidence_badge_html(row.get('AI_CONFIDENCE'))}</div></td>"
                f"<td class='recent-claims-td sticky-actions-cell' style='width:{RECENT_CLAIMS_WIDTH_MAP['ACTIONS']}px'><button class='review-link' type='button' data-claim-id='{escape(claim_id)}'>Review</button></td>"
                "</tr>"
            )
        recent_claims_css = _load_recent_claims_table_css()
        table_html = (
            f"<style>{recent_claims_css}</style>"
            "<div class='recent-claims-table-frame'>"
            "<div class='table-top-scrollbar' aria-hidden='true'><div class='table-top-scrollbar-spacer'></div></div>"
            "<div class='recent-claims-table-wrapper'><table class='recent-claims-table'><thead><tr>"
            + "".join(header_cells)
            + "</tr></thead><tbody class='recent-claims-tbody'>"
            + "".join(rows_html)
            + "</tbody></table></div>"
            "</div>"
            + _top_scroll_sync_script(
                '.recent-claims-table-frame', '.recent-claims-table-wrapper', '.recent-claims-table'
            )
            + _recent_claims_sort_script()
        )
        review_event = _RECENT_CLAIMS_TABLE_COMPONENT(
            html=table_html,
            height=600,
            key=stable_component_key,
            default=None,
        )
        if isinstance(review_event, dict):
            claim_id = str(review_event.get("claim_id", "")).strip()
            event_id = str(review_event.get("event_id", "")).strip()
            last_event_key = f"{key_prefix}_recent_claims_last_review_event_id"
            last_processed_claim_id = str(st.session_state.get("last_processed_review_claim_id", "")).strip()
            is_new_event = bool(event_id) and st.session_state.get(last_event_key) != event_id
            is_new_claim_without_event_id = bool(claim_id) and not event_id and claim_id != last_processed_claim_id
            if claim_id and (is_new_event or is_new_claim_without_event_id):
                st.session_state[last_event_key] = event_id
                st.session_state["last_review_event"] = None
                _open_claim_details(claim_id)
        summary_text = f"Showing {start_idx + 1}-{end_idx} of {total_claims} claims"
        pager_cols = st.columns([3, 1], vertical_alignment="center")
        pager_cols[0].markdown(f"<div class='recent-claims-pagination-summary'>{summary_text}</div>", unsafe_allow_html=True)
        with pager_cols[1]:
            prev_col, next_col = st.columns(2)
            with prev_col:
                if st.button("Previous", key=f"{pagination_key_base}_prev", disabled=current_page <= 1, use_container_width=True):
                    st.session_state[page_state_key] = max(1, current_page - 1)
                    st.rerun()
            with next_col:
                if st.button("Next", key=f"{pagination_key_base}_next", disabled=current_page >= total_pages, use_container_width=True):
                    st.session_state[page_state_key] = min(total_pages, current_page + 1)
                    st.rerun()
