from __future__ import annotations

from datetime import date, timedelta
from html import escape
import logging
from time import perf_counter

import streamlit as st

from components.cards import render_kpi_cards
from components.tables import render_recent_claims_table
from pages import claim_details
from services.claim_service import (
    get_available_claim_statuses,
    get_available_claim_types,
    get_filtered_claims_count,
    get_filtered_recent_claims,
)
from services.dashboard_service import get_dashboard_metrics
from services.rbac_service import get_session_context_snapshot

logger = logging.getLogger(__name__)

DASHBOARD_RECENT_CLAIMS_PAGE_SIZE = 10
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


def _dashboard_filters() -> dict[str, object]:
    return {
        "selected_statuses": _selected_list("selected_statuses"),
        "selected_priorities": _selected_list("selected_priorities"),
        "selected_ai_confidence_buckets": _selected_list("selected_ai_confidence_buckets"),
        "selected_claim_types": _selected_list("selected_claim_types"),
        "date_requested_from": st.session_state.get("date_requested_from"),
        "date_requested_to": st.session_state.get("date_requested_to"),
        "search_text": str(st.session_state.get("dash_recent_claims_search") or ""),
    }


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


def _render_dashboard_filter_controls(session) -> None:
    if st.session_state.pop("dashboard_filters_clear_requested", False):
        _clear_all_dashboard_filters_before_widgets()

    status_options = _merge_filter_options(STATUS_FILTER_OPTIONS, get_available_claim_statuses(session))
    claim_type_options = _merge_filter_options([], get_available_claim_types(session))

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


def _render_dashboard_header(session, display_name: str) -> None:
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
                    _render_dashboard_filter_controls(session)
            else:
                with st.expander("Filters", expanded=False):
                    _render_dashboard_filter_controls(session)
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
    _render_dashboard_header(session, display_name)

    t0 = perf_counter()
    session_ctx = get_session_context_snapshot(session)
    session_ctx["selected_sf_role"] = str(st.session_state.get("selected_sf_role") or "")
    logger.info("dashboard_session_context=%s", session_ctx)
    metrics = get_dashboard_metrics(session, username=ctx.username)
    logger.info("dashboard_metrics_ms=%d", int((perf_counter() - t0) * 1000))
    render_kpi_cards(metrics)

    card_key = "dash_recent_claims"
    search = st.session_state.get(f"{card_key}_search", "")

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
                    search = st.text_input(
                        "Search",
                        value=search,
                        placeholder="Search by patient, file #...",
                        label_visibility="collapsed",
                        key=f"{card_key}_search",
                    )

        previous_search = st.session_state.get(f"{card_key}_prev_search", "")
        if str(previous_search) != str(search):
            st.session_state["claims_page_number"] = 1
            st.session_state["dash_recent_claims_pagination_page"] = 1
        st.session_state[f"{card_key}_prev_search"] = search

        filters = _dashboard_filters()
        requested_page = max(1, int(st.session_state.get("claims_page_number", 1)))
        t1 = perf_counter()
        total_claims = get_filtered_claims_count(session, filters)
        total_pages = max(1, (total_claims + DASHBOARD_RECENT_CLAIMS_PAGE_SIZE - 1) // DASHBOARD_RECENT_CLAIMS_PAGE_SIZE)
        current_page = min(requested_page, total_pages)
        if current_page != requested_page:
            st.session_state["claims_page_number"] = current_page
        recent_claims = get_filtered_recent_claims(session, filters, current_page, DASHBOARD_RECENT_CLAIMS_PAGE_SIZE)
        logger.info(
            "dashboard_recent_claims_ms=%d rows=%d total=%d filters=%s",
            int((perf_counter() - t1) * 1000),
            len(recent_claims),
            total_claims,
            filters,
        )

        render_recent_claims_table(
            recent_claims,
            key_prefix="dash",
            empty_message="No claims found for the selected filters.",
            total_claims=total_claims,
            page=current_page,
            page_size=DASHBOARD_RECENT_CLAIMS_PAGE_SIZE,
            pagination_state_key="claims_page_number",
        )


def render(session, ctx) -> None:
    if "current_view" not in st.session_state:
        st.session_state["current_view"] = "dashboard"

    if st.session_state.get("current_view") in {"Claim Details", "claim_details"} and st.session_state.get("selected_claim_id"):
        logger.info("render_claim_details called claim_id=%s", st.session_state.get("selected_claim_id"))
        claim_details.render(session=session, ctx=ctx)
        st.stop()

    if st.session_state.get("current_view") in {"dashboard", "Dashboard"}:
        _render_dashboard_view(session=session, ctx=ctx)
        st.stop()

    # Fallback to dashboard when state is unknown.
    st.session_state["current_view"] = "dashboard"
    _render_dashboard_view(session=session, ctx=ctx)
    st.stop()
