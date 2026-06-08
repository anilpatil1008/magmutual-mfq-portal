from __future__ import annotations

from datetime import date, timedelta
from html import escape
import logging
from time import perf_counter

import streamlit as st

from components.cards import render_kpi_cards
from components.tables import render_live_claims_search, render_recent_claims_table
from services.claim_service import (
    get_available_claim_statuses,
    get_available_claim_types,
    get_cached_recent_claims,
    get_filtered_claims_count_local,
    get_filtered_recent_claims_local,
)
from services.dashboard_service import get_dashboard_metrics
from services.rbac_service import get_session_context_snapshot
from utils.navigation import DASHBOARD_VIEW

logger = logging.getLogger(__name__)

DASHBOARD_RECENT_CLAIMS_PAGE_SIZE = 10
CLAIM_BUCKET_OPTIONS = ("ongoing", "history")
CLAIM_BUCKET_LABELS = {"ongoing": "Ongoing Claims", "history": "History Claims"}
STATUS_FILTER_OPTIONS = ["MFQ Generated", "Assigned", "Approved", "Rejected"]
PRIORITY_FILTER_OPTIONS = ["High", "Medium", "Low"]
AI_CONFIDENCE_FILTER_OPTIONS = [
    ("High", "High (90%+)"),
    ("Medium", "Medium (80-89%)"),
    ("Low", "Low (<80%)"),
]
DATE_REQUESTED_QUICK_FILTERS = [
    "All Dates",
    "Today",
    "Last 7 Days",
    "Last 30 Days",
    "This Month",
]


def _init_dashboard_filter_state() -> None:
    legacy_status = st.session_state.pop("selected_status", None)
    legacy_priority = st.session_state.pop("selected_priority", None)
    legacy_ai_confidence = st.session_state.pop("selected_ai_confidence", None)
    defaults = {
        "selected_statuses": [],
        "selected_priorities": [],
        "selected_ai_confidence_buckets": [],
        "selected_claim_types": [],
        "date_requested_from": None,
        "date_requested_to": None,
        "date_requested_from_widget": None,
        "date_requested_to_widget": None,
        "claims_page_number": 1,
        "dash_recent_claims_search": "",
        "dash_ongoing_claims_search": "",
        "dash_history_claims_search": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    legacy_migrations = (
        (legacy_status, "All Statuses", "selected_statuses"),
        (legacy_priority, "All Priorities", "selected_priorities"),
        (legacy_ai_confidence, "All Scores", "selected_ai_confidence_buckets"),
    )
    for legacy_value, all_label, state_key in legacy_migrations:
        if legacy_value and legacy_value != all_label and not st.session_state.get(state_key):
            st.session_state[state_key] = [str(legacy_value)]


def _reset_recent_claims_pagination() -> None:
    st.session_state["claims_page_number"] = 1
    st.session_state["dash_recent_claims_pagination_page"] = 1


def _filter_button_slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value)).strip("_") or "blank"


def _selected_list(state_key: str) -> list[str]:
    value = st.session_state.get(state_key, [])
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if isinstance(value, tuple | set):
        return [str(item) for item in value if str(item or "").strip()]
    return [str(value)] if str(value or "").strip() else []


def _toggle_dashboard_multi_filter(state_key: str, value: str, all_label: str | None = None) -> None:
    current_values = _selected_list(state_key)
    if all_label and value == all_label:
        new_values = []
    elif value in current_values:
        new_values = [item for item in current_values if item != value]
    else:
        new_values = [*current_values, value]

    if current_values != new_values:
        st.session_state[state_key] = new_values
        _reset_recent_claims_pagination()
        st.rerun()


def _render_filter_chip_group(
    title: str,
    state_key: str,
    options: list[str] | list[tuple[str, str]],
    group_key: str,
    all_label: str,
) -> None:
    st.markdown(f"<p class='mfq-filter-section-label'>{escape(title)}</p>", unsafe_allow_html=True)
    options_with_all: list[str] | list[tuple[str, str]] = [all_label, *options]
    columns = st.columns(3, gap="small")
    selected_values = _selected_list(state_key)
    for index, option in enumerate(options_with_all):
        value, label = option if isinstance(option, tuple) else (option, option)
        selected = not selected_values if value == all_label else value in selected_values
        state_suffix = "selected" if selected else "unselected"
        chip_key = f"filter_chip_{group_key}_{_filter_button_slug(str(value))}_{state_suffix}"
        with columns[index % 3]:
            with st.container(key=chip_key):
                if st.button(str(label), key=f"{chip_key}_button", use_container_width=True):
                    _toggle_dashboard_multi_filter(state_key, str(value), all_label=all_label)


def _set_date_requested_quick_filter(label: str) -> None:
    today = date.today()
    if label == "All Dates":
        from_date = None
        to_date = None
    elif label == "Today":
        from_date = today
        to_date = today
    elif label == "Last 7 Days":
        from_date = today - timedelta(days=6)
        to_date = today
    elif label == "Last 30 Days":
        from_date = today - timedelta(days=29)
        to_date = today
    elif label == "This Month":
        from_date = today.replace(day=1)
        to_date = today
    else:
        return

    if st.session_state.get("date_requested_from") != from_date or st.session_state.get("date_requested_to") != to_date:
        st.session_state["date_requested_from"] = from_date
        st.session_state["date_requested_to"] = to_date
        st.session_state["date_requested_from_widget"] = from_date
        st.session_state["date_requested_to_widget"] = to_date
        _reset_recent_claims_pagination()
        st.rerun()


def _date_quick_filter_is_selected(label: str) -> bool:
    from_date = st.session_state.get("date_requested_from")
    to_date = st.session_state.get("date_requested_to")
    today = date.today()
    if label == "All Dates":
        return from_date is None and to_date is None
    if label == "Today":
        return from_date == today and to_date == today
    if label == "Last 7 Days":
        return from_date == today - timedelta(days=6) and to_date == today
    if label == "Last 30 Days":
        return from_date == today - timedelta(days=29) and to_date == today
    if label == "This Month":
        return from_date == today.replace(day=1) and to_date == today
    return False


def _render_date_requested_filter() -> None:
    st.markdown("<p class='mfq-filter-section-label'>Date Requested</p>", unsafe_allow_html=True)
    chip_columns = st.columns(3, gap="small")
    for index, label in enumerate(DATE_REQUESTED_QUICK_FILTERS):
        selected = _date_quick_filter_is_selected(label)
        state_suffix = "selected" if selected else "unselected"
        chip_key = f"filter_chip_date_requested_{_filter_button_slug(label)}_{state_suffix}"
        with chip_columns[index % 3]:
            with st.container(key=chip_key):
                if st.button(label, key=f"{chip_key}_button", use_container_width=True):
                    _set_date_requested_quick_filter(label)

    from_col, to_col = st.columns(2, gap="small")
    with from_col:
        from_date = st.date_input(
            "From Date",
            value=st.session_state.get("date_requested_from"),
            key="date_requested_from_widget",
            format="MM/DD/YYYY",
            on_change=_reset_recent_claims_pagination,
        )
    with to_col:
        to_date = st.date_input(
            "To Date",
            value=st.session_state.get("date_requested_to"),
            key="date_requested_to_widget",
            format="MM/DD/YYYY",
            on_change=_reset_recent_claims_pagination,
        )

    if st.session_state.get("date_requested_from") != from_date:
        st.session_state["date_requested_from"] = from_date
    if st.session_state.get("date_requested_to") != to_date:
        st.session_state["date_requested_to"] = to_date


def _clear_all_dashboard_filters_before_widgets() -> None:
    st.session_state.update(
        {
            "selected_statuses": [],
            "selected_priorities": [],
            "selected_ai_confidence_buckets": [],
            "selected_claim_types": [],
            "date_requested_from": None,
            "date_requested_to": None,
            "date_requested_from_widget": None,
            "date_requested_to_widget": None,
            "claims_page_number": 1,
            "dash_recent_claims_pagination_page": 1,
        }
    )


def _active_dashboard_filter_count() -> int:
    count = sum(
        len(_selected_list(key))
        for key in (
            "selected_statuses",
            "selected_priorities",
            "selected_ai_confidence_buckets",
            "selected_claim_types",
        )
    )
    if st.session_state.get("date_requested_from") is not None:
        count += 1
    if st.session_state.get("date_requested_to") is not None:
        count += 1
    return count


def _dashboard_filters(search_text: str = "") -> dict[str, object]:
    return {
        "selected_statuses": _selected_list("selected_statuses"),
        "selected_priorities": _selected_list("selected_priorities"),
        "selected_ai_confidence_buckets": _selected_list("selected_ai_confidence_buckets"),
        "selected_claim_types": _selected_list("selected_claim_types"),
        "date_requested_from": st.session_state.get("date_requested_from"),
        "date_requested_to": st.session_state.get("date_requested_to"),
        "search_text": str(search_text or ""),
    }


def _claims_search_state_key(claim_bucket: str) -> str:
    bucket_key = str(claim_bucket or "recent").strip().lower()
    if bucket_key in {"ongoing", "history"}:
        return f"dash_{bucket_key}_claims_search"
    return "dash_recent_claims_search"


def _claims_search_text(claim_bucket: str) -> str:
    return str(st.session_state.get(_claims_search_state_key(claim_bucket)) or "")


def _claim_bucket_filters(filters: dict[str, object], claim_bucket: str, search_text: str | None = None) -> dict[str, object]:
    bucket_filters = dict(filters)
    bucket_filters["claim_bucket"] = claim_bucket
    if search_text is not None:
        bucket_filters["search_text"] = str(search_text or "")
    return bucket_filters


def _claim_bucket_label(claim_bucket: str, counts: dict[str, int]) -> str:
    label = CLAIM_BUCKET_LABELS.get(claim_bucket, str(claim_bucket).title())
    return f"{label} ({counts.get(claim_bucket, 0)})"


def _reset_claims_page_on_context_change(card_key: str, selected_bucket: str, search: str) -> None:
    previous_bucket = st.session_state.get(f"{card_key}_prev_bucket")
    previous_search = st.session_state.get(f"{card_key}_prev_search", "")
    if previous_bucket != selected_bucket or str(previous_search) != str(search):
        _reset_recent_claims_pagination()
    st.session_state[f"{card_key}_prev_bucket"] = selected_bucket
    st.session_state[f"{card_key}_prev_search"] = search


def _merge_filter_options(default_options: list[str], dynamic_options: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in [*default_options, *dynamic_options]:
        normalized = str(value or "").strip()
        upper_value = normalized.upper()
        if normalized and upper_value not in seen:
            merged.append(normalized)
            seen.add(upper_value)
    return merged


def _values_from_claims(claims, column_name: str) -> list[str]:
    if column_name not in claims.columns:
        return []
    values = claims[column_name].dropna().astype(str).str.strip()
    return sorted({value for value in values.tolist() if value}, key=str.upper)


def _render_dashboard_filter_controls(session, claims=None) -> None:
    if st.session_state.pop("dashboard_filters_clear_requested", False):
        _clear_all_dashboard_filters_before_widgets()

    status_options = _merge_filter_options(
        STATUS_FILTER_OPTIONS,
        _values_from_claims(claims, "MFQ_STATUS") if claims is not None else get_available_claim_statuses(session),
    )
    claim_type_options = _merge_filter_options(
        [],
        _values_from_claims(claims, "CLAIM_TYPE") if claims is not None else get_available_claim_types(session),
    )

    st.markdown(
        "<div class='mfq-dashboard-filter-panel-marker'></div>"
        "<div class='mfq-filter-popover-heading'>Filter Claims</div>",
        unsafe_allow_html=True,
    )
    _render_filter_chip_group("Status", "selected_statuses", status_options, "status", "All Statuses")
    _render_filter_chip_group("Priority", "selected_priorities", PRIORITY_FILTER_OPTIONS, "priority", "All Priorities")
    _render_filter_chip_group("Claim Type", "selected_claim_types", claim_type_options, "claim_type", "All Claim Types")
    _render_filter_chip_group(
        "AI Confidence Score",
        "selected_ai_confidence_buckets",
        AI_CONFIDENCE_FILTER_OPTIONS,
        "ai_confidence",
        "All Scores",
    )
    _render_date_requested_filter()
    st.markdown("<div class='mfq-filter-clear-all'></div>", unsafe_allow_html=True)
    if st.button("Clear All Filters", key="dashboard_clear_all_filters", use_container_width=True):
        st.session_state["dashboard_filters_clear_requested"] = True
        st.rerun()


def _render_dashboard_header(session, display_name: str, claims=None) -> None:
    header_left, header_right = st.columns([8, 2], vertical_alignment="top")
    with header_left:
        st.title("Dashboard")
        if display_name:
            st.markdown(
                (
                    f"<p class='mm-dashboard-welcome'>Welcome back, {escape(display_name)}. "
                    "Here's what's happening today.</p>"
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<p class='mm-dashboard-welcome'>Welcome back. Here's what's happening today.</p>",
                unsafe_allow_html=True,
            )
    with header_right:
        with st.container(key="dashboard_header_actions"):
            st.markdown("<div class='dashboard-filter-button-wrapper'>", unsafe_allow_html=True)
            if hasattr(st, "popover"):
                active_filter_count = _active_dashboard_filter_count()
                filter_label = f"Filters ({active_filter_count})" if active_filter_count else "Filters"
                with st.popover(
                    filter_label,
                    icon=":material/filter_list:",
                    width="content",
                    key="dashboard_filters_popover",
                ):
                    _render_dashboard_filter_controls(session, claims)
            else:
                with st.expander("Filters", expanded=False):
                    _render_dashboard_filter_controls(session, claims)
            st.markdown("</div>", unsafe_allow_html=True)


def _resolve_user_display_name(ctx) -> str:
    candidate_values = [
        getattr(ctx, "full_name", None),
        getattr(ctx, "name", None),
        st.session_state.get("full_name"),
        st.session_state.get("user_full_name"),
        st.session_state.get("username"),
        st.session_state.get("user_email"),
    ]

    user_profile = st.session_state.get("user_profile")
    if isinstance(user_profile, dict):
        candidate_values.extend(
            [
                user_profile.get("full_name"),
                user_profile.get("name"),
                user_profile.get("username"),
                user_profile.get("email"),
            ]
        )

    for candidate in candidate_values:
        value = str(candidate or "").strip()
        if value:
            return value

    return str(getattr(ctx, "username", "") or "").strip()


def _render_dashboard_view(session, ctx) -> None:
    logger.info("render_dashboard called")
    _init_dashboard_filter_state()
    display_name = _resolve_user_display_name(ctx)

    recent_claims_dataset = get_cached_recent_claims(session)
    _render_dashboard_header(session, display_name, recent_claims_dataset)

    t0 = perf_counter()
    session_ctx = get_session_context_snapshot(session)
    session_ctx["selected_sf_role"] = str(st.session_state.get("selected_sf_role") or "")
    logger.info("dashboard_session_context=%s", session_ctx)
    metrics = get_dashboard_metrics(session, username=ctx.username)
    logger.info("dashboard_metrics_ms=%d", int((perf_counter() - t0) * 1000))
    render_kpi_cards(metrics)

    card_key = "dashboard_claims"
    selected_bucket_for_search = str(st.session_state.get("dashboard_claims_tab") or CLAIM_BUCKET_OPTIONS[0])
    if selected_bucket_for_search not in CLAIM_BUCKET_OPTIONS:
        selected_bucket_for_search = CLAIM_BUCKET_OPTIONS[0]
    search_state_key = _claims_search_state_key(selected_bucket_for_search)
    search = _claims_search_text(selected_bucket_for_search)

    with st.container(key="recent_claims_card"):
        with st.container(key="recent_claims_toolbar"):
            header_left, header_right = st.columns([4, 2], vertical_alignment="top")
            with header_left:
                st.markdown(
                    (
                        "<div class='recent-claims-heading'>"
                        "<h3 class='recent-claims-title'>Recent Claims</h3>"
                        "<p class='recent-claims-subtitle'>Latest claims submitted for assessment.</p>"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )
            with header_right:
                with st.container(key="recent_claims_search"):
                    live_search = render_live_claims_search(
                        value=search,
                        table_key="dashboard_claims_search",
                        placeholder="Search by patient, defendant, claim ID, file #, or status...",
                    )
                    if live_search is not None and live_search != search:
                        st.session_state[search_state_key] = live_search
                        search = live_search

        filters = _dashboard_filters(search)
        t1 = perf_counter()
        claim_counts = {
            bucket: get_filtered_claims_count_local(
                recent_claims_dataset,
                _claim_bucket_filters(_dashboard_filters(_claims_search_text(bucket)), bucket),
            )
            for bucket in CLAIM_BUCKET_OPTIONS
        }

        selected_bucket = st.radio(
            "Recent Claims Tabs",
            CLAIM_BUCKET_OPTIONS,
            horizontal=True,
            key="dashboard_claims_tab",
            format_func=lambda bucket: _claim_bucket_label(bucket, claim_counts),
            label_visibility="collapsed",
        )
        if selected_bucket != selected_bucket_for_search:
            search = _claims_search_text(selected_bucket)
            filters = _dashboard_filters(search)
        _reset_claims_page_on_context_change(card_key, selected_bucket, search)

        bucket_filters = _claim_bucket_filters(filters, selected_bucket, search)
        total_claims = claim_counts[selected_bucket]
        requested_page = max(1, int(st.session_state.get("claims_page_number", 1)))
        total_pages = max(1, (total_claims + DASHBOARD_RECENT_CLAIMS_PAGE_SIZE - 1) // DASHBOARD_RECENT_CLAIMS_PAGE_SIZE)
        current_page = min(requested_page, total_pages)
        if current_page != requested_page:
            st.session_state["claims_page_number"] = current_page
        recent_claims = get_filtered_recent_claims_local(
            recent_claims_dataset,
            bucket_filters,
            current_page,
            DASHBOARD_RECENT_CLAIMS_PAGE_SIZE,
        )
        logger.info(
            "dashboard_recent_claims_ms=%d bucket=%s rows=%d total=%d filters=%s",
            int((perf_counter() - t1) * 1000),
            selected_bucket,
            len(recent_claims),
            total_claims,
            bucket_filters,
        )

        render_recent_claims_table(
            recent_claims,
            key_prefix="dash",
            empty_message=(
                "No matching claims found"
                if search.strip()
                else
                "No ongoing claims found for the selected filters."
                if selected_bucket == "ongoing"
                else "No history claims found for the selected filters."
            ),
            total_claims=total_claims,
            page=current_page,
            page_size=DASHBOARD_RECENT_CLAIMS_PAGE_SIZE,
            pagination_state_key="claims_page_number",
            table_key="recent_claims_table",
            component_key="recent_claims_table",
        )


def render(session, ctx) -> None:
    """Render the single active Dashboard implementation once for this router pass."""
    if str(st.session_state.get("current_view") or DASHBOARD_VIEW).strip().lower() != DASHBOARD_VIEW:
        return

    _render_dashboard_view(session=session, ctx=ctx)
