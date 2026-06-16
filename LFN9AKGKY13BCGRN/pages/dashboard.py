from __future__ import annotations

from datetime import date, timedelta
from html import escape
import logging
from time import perf_counter

import streamlit as st
from utils.streamlit_compat import (
    safe_button,
    safe_columns,
    safe_container,
    safe_popover,
    safe_rerun,
)

from components.cards import render_kpi_cards
from components.tables import render_live_claims_search, render_recent_claims_table
import services.claim_service as claim_service
from services.dashboard_service import get_dashboard_metrics
from services.rbac_service import get_session_context_snapshot
from utils import navigation

logger = logging.getLogger(__name__)

DASHBOARD_CLAIMS_VIEW_FALLBACK_OPTIONS = ("ongoing", "history")
DASHBOARD_CLAIMS_VIEW_FALLBACK_DEFAULT = "ongoing"
DASHBOARD_VIEW = getattr(navigation, "DASHBOARD_VIEW", "dashboard")
# Keep dashboard import-safe when an older navigation module is loaded from
# cache or an out-of-date deployment. The Dashboard page owns these fallback
# values because it must be able to import before any navigation-state repair
# logic can run.
CLAIM_BUCKET_OPTIONS = tuple(
    getattr(
        navigation,
        "DASHBOARD_CLAIMS_VIEW_OPTIONS",
        DASHBOARD_CLAIMS_VIEW_FALLBACK_OPTIONS,
    )
)
if not CLAIM_BUCKET_OPTIONS:
    CLAIM_BUCKET_OPTIONS = DASHBOARD_CLAIMS_VIEW_FALLBACK_OPTIONS
CLAIM_BUCKET_LABELS = {
    "recent": "Recent Claims",
    "ongoing": "Ongoing Claims",
    "history": "History Claims",
}
CLAIM_BUCKET_DEFAULT = getattr(
    navigation,
    "DASHBOARD_CLAIMS_VIEW_DEFAULT",
    DASHBOARD_CLAIMS_VIEW_FALLBACK_DEFAULT,
)
if CLAIM_BUCKET_DEFAULT not in CLAIM_BUCKET_OPTIONS:
    CLAIM_BUCKET_DEFAULT = DASHBOARD_CLAIMS_VIEW_FALLBACK_DEFAULT
CLAIM_BUCKET_STATE_KEY = getattr(
    navigation,
    "DASHBOARD_CLAIMS_VIEW_STATE_KEY",
    "selected_claim_view",
)
CLAIM_BUCKET_LEGACY_STATE_KEY = getattr(
    navigation,
    "DASHBOARD_CLAIMS_VIEW_LEGACY_STATE_KEY",
    "claim_scope",
)



RECENT_CLAIMS_VIEW_STATE_KEY = "recent_claims_view"
RECENT_CLAIMS_VIEW_RADIO_KEY = "recent_claims_view_radio"
STATUS_FILTER_OPTIONS = ["MFQ Generated", "Assigned", "Approved", "Rejected", "On Hold"]
HIDDEN_STATUS_FILTER_VALUES = {
    "INTAKE_COMPLETE",
    "READY_FOR_EMBEDDING",
    "INSUFFICIENT_EVIDENCE",
    "INSUFFICIENT_EVIDEN",
    "FAILED",
}
PRIORITY_FILTER_OPTIONS = ["High", "Medium", "Low"]
AI_CONFIDENCE_FILTER_OPTIONS = [
    ("High", "More than 90%"),
    ("Medium", "75-90%"),
    ("Low", "Less than 75%"),
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
    canonical_claim_view_missing = CLAIM_BUCKET_STATE_KEY not in st.session_state
    recent_claims_view_missing = RECENT_CLAIMS_VIEW_STATE_KEY not in st.session_state
    defaults = {
        "selected_statuses": [],
        "selected_priorities": [],
        "selected_ai_confidence_buckets": [],
        "selected_claim_types": [],
        "date_requested_from": None,
        "date_requested_to": None,
        "date_requested_widget_version": 0,
        "dash_recent_claims_search": "",
        "dash_ongoing_claims_search": "",
        "dash_history_claims_search": "",
        CLAIM_BUCKET_STATE_KEY: CLAIM_BUCKET_DEFAULT,
        CLAIM_BUCKET_LEGACY_STATE_KEY: CLAIM_BUCKET_DEFAULT,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    legacy_scope = st.session_state.pop("dashboard_claims_tab", None)
    if legacy_scope not in CLAIM_BUCKET_OPTIONS:
        legacy_scope = st.session_state.get(CLAIM_BUCKET_LEGACY_STATE_KEY)

    recent_claims_view = (
        str(st.session_state.get(RECENT_CLAIMS_VIEW_STATE_KEY) or "").strip().lower()
    )
    current_scope = (
        str(st.session_state.get(CLAIM_BUCKET_STATE_KEY) or "").strip().lower()
    )
    if recent_claims_view in CLAIM_BUCKET_OPTIONS and not recent_claims_view_missing:
        current_scope = recent_claims_view
    elif canonical_claim_view_missing and legacy_scope in CLAIM_BUCKET_OPTIONS:
        current_scope = str(legacy_scope)
    elif (
        current_scope not in CLAIM_BUCKET_OPTIONS
        and legacy_scope in CLAIM_BUCKET_OPTIONS
    ):
        current_scope = str(legacy_scope)
    elif current_scope not in CLAIM_BUCKET_OPTIONS:
        current_scope = CLAIM_BUCKET_DEFAULT

    st.session_state[RECENT_CLAIMS_VIEW_STATE_KEY] = current_scope
    st.session_state[RECENT_CLAIMS_VIEW_RADIO_KEY] = current_scope
    st.session_state[CLAIM_BUCKET_STATE_KEY] = current_scope
    st.session_state[CLAIM_BUCKET_LEGACY_STATE_KEY] = current_scope

    legacy_migrations = (
        (legacy_status, "All Statuses", "selected_statuses"),
        (legacy_priority, "All Priorities", "selected_priorities"),
        (legacy_ai_confidence, "All Scores", "selected_ai_confidence_buckets"),
    )
    for legacy_value, all_label, state_key in legacy_migrations:
        if (
            legacy_value
            and legacy_value != all_label
            and not st.session_state.get(state_key)
        ):
            st.session_state[state_key] = [str(legacy_value)]



def _refresh_date_requested_widgets() -> None:
    current_version = int(st.session_state.get("date_requested_widget_version", 0) or 0)
    st.session_state["date_requested_widget_version"] = current_version + 1


def _filter_button_slug(value: str) -> str:
    return (
        "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value)).strip("_")
        or "blank"
    )


def _selected_list(state_key: str) -> list[str]:
    value = st.session_state.get(state_key, [])
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if isinstance(value, tuple | set):
        return [str(item) for item in value if str(item or "").strip()]
    return [str(value)] if str(value or "").strip() else []


def _toggle_dashboard_multi_filter(
    state_key: str, value: str, all_label: str | None = None
) -> None:
    current_values = _selected_list(state_key)
    if all_label and value == all_label:
        new_values = []
    elif value in current_values:
        new_values = [item for item in current_values if item != value]
    else:
        new_values = [*current_values, value]

    if current_values != new_values:
        st.session_state[state_key] = new_values
        safe_rerun()


def _filter_chip_tone_class(group_key: str, value: str) -> str:
    normalized_value = str(value or "").strip().lower()
    slug = _filter_button_slug(normalized_value)
    group_slug = _filter_button_slug(group_key)

    tone_aliases = {
        "all_statuses": "all",
        "all_priorities": "all",
        "all_claim_types": "all",
        "all_scores": "all",
        "mfq_generated": "generated",
        "on_hold": "onhold",
        "more_than_90": "high",
        "75_90": "medium",
        "less_than_75": "low",
        "suit": "suit",
        "claim": "claim",
    }
    tone = tone_aliases.get(slug, slug or "unknown")

    if group_slug == "ai_confidence":
        group_slug = "confidence"
    elif group_slug == "claim_type":
        group_slug = "claimtype"

    return f"mfq-chip-{group_slug}-{tone}"


def _render_filter_chip_group(
    title: str,
    state_key: str,
    options: list[str] | list[tuple[str, str]],
    group_key: str,
    all_label: str,
) -> None:
    st.markdown(
        f"<p class='mfq-filter-section-label'>{escape(title)}</p>",
        unsafe_allow_html=True,
    )
    options_with_all: list[str] | list[tuple[str, str]] = [all_label, *options]
    columns = safe_columns(3, gap="small")
    selected_values = _selected_list(state_key)
    for index, option in enumerate(options_with_all):
        value, label = option if isinstance(option, tuple) else (option, option)
        selected = (
            not selected_values if value == all_label else value in selected_values
        )
        state_suffix = "selected" if selected else "unselected"
        chip_tone_class = _filter_chip_tone_class(group_key, str(value))
        chip_key = f"filter_chip_{group_key}_{_filter_button_slug(str(value))}_{chip_tone_class}_{state_suffix}"
        with columns[index % 3]:
            with safe_container(key=chip_key):
                if safe_button(
                    str(label), key=f"{chip_key}_button", use_container_width=True
                ):
                    _toggle_dashboard_multi_filter(
                        state_key, str(value), all_label=all_label
                    )


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

    if (
        st.session_state.get("date_requested_from") != from_date
        or st.session_state.get("date_requested_to") != to_date
    ):
        st.session_state["date_requested_from"] = from_date
        st.session_state["date_requested_to"] = to_date
        _refresh_date_requested_widgets()
        safe_rerun()


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
    st.markdown(
        "<p class='mfq-filter-section-label'>Date Requested</p>", unsafe_allow_html=True
    )
    chip_columns = safe_columns(3, gap="small")
    for index, label in enumerate(DATE_REQUESTED_QUICK_FILTERS):
        selected = _date_quick_filter_is_selected(label)
        state_suffix = "selected" if selected else "unselected"
        chip_key = f"filter_chip_date_requested_{_filter_button_slug(label)}_mfq-chip-date-all_{state_suffix}"
        with chip_columns[index % 3]:
            with safe_container(key=chip_key):
                if safe_button(
                    label, key=f"{chip_key}_button", use_container_width=True
                ):
                    _set_date_requested_quick_filter(label)

    widget_version = int(st.session_state.get("date_requested_widget_version", 0) or 0)
    from_col, to_col = safe_columns(2, gap="small")
    with from_col:
        from_date = st.date_input(
            "From Date",
            value=st.session_state.get("date_requested_from"),
            key=f"date_requested_from_widget_{widget_version}",
            format="MM/DD/YYYY",
        )
    with to_col:
        to_date = st.date_input(
            "To Date",
            value=st.session_state.get("date_requested_to"),
            key=f"date_requested_to_widget_{widget_version}",
            format="MM/DD/YYYY",
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
                        "dash_recent_claims_search": "",
            "dash_ongoing_claims_search": "",
            "dash_history_claims_search": "",
            RECENT_CLAIMS_VIEW_STATE_KEY: CLAIM_BUCKET_DEFAULT,
            RECENT_CLAIMS_VIEW_RADIO_KEY: CLAIM_BUCKET_DEFAULT,
            CLAIM_BUCKET_STATE_KEY: CLAIM_BUCKET_DEFAULT,
            CLAIM_BUCKET_LEGACY_STATE_KEY: CLAIM_BUCKET_DEFAULT,
        }
    )
    _refresh_date_requested_widgets()


def _clear_all_dashboard_filters() -> None:
    # Streamlit disallows editing widget-backed session state after that widget
    # has been instantiated during the same script run. Keep this function wired
    # as the clear button callback so it runs before widgets are recreated.
    _clear_all_dashboard_filters_before_widgets()
    st.session_state.pop("dashboard_filtered_claims_count", None)
    st.session_state.pop("dashboard_filtered_claims_cache", None)


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
        "selected_ai_confidence_buckets": _selected_list(
            "selected_ai_confidence_buckets"
        ),
        "selected_claim_types": _selected_list("selected_claim_types"),
        "date_requested_from": st.session_state.get("date_requested_from"),
        "date_requested_to": st.session_state.get("date_requested_to"),
        "search_text": str(search_text or ""),
    }


def _claims_search_state_key(claim_bucket: str) -> str:
    bucket_key = str(claim_bucket or "recent").strip().lower()
    if bucket_key in {"recent", "ongoing", "history"}:
        return f"dash_{bucket_key}_claims_search"
    return "dash_recent_claims_search"


def _claims_search_text(claim_bucket: str) -> str:
    return str(st.session_state.get(_claims_search_state_key(claim_bucket)) or "")


def _claim_bucket_filters(
    filters: dict[str, object], claim_bucket: str, search_text: str | None = None
) -> dict[str, object]:
    bucket_filters = dict(filters)
    normalized_bucket = str(claim_bucket or "").strip().lower()
    if normalized_bucket in {"ongoing", "history"}:
        bucket_filters["claim_bucket"] = normalized_bucket
    else:
        bucket_filters.pop("claim_bucket", None)
    if search_text is not None:
        bucket_filters["search_text"] = str(search_text or "")
    return bucket_filters


def _claim_bucket_label(claim_bucket: str, counts: dict[str, int]) -> str:
    label = CLAIM_BUCKET_LABELS.get(claim_bucket, str(claim_bucket).title())
    return f"{label} ({counts.get(claim_bucket, 0)})"


def _on_recent_claims_view_change() -> None:
    selected_view = (
        str(st.session_state.get(RECENT_CLAIMS_VIEW_RADIO_KEY) or CLAIM_BUCKET_DEFAULT)
        .strip()
        .lower()
    )
    if selected_view not in CLAIM_BUCKET_OPTIONS:
        selected_view = CLAIM_BUCKET_DEFAULT

    st.session_state[RECENT_CLAIMS_VIEW_STATE_KEY] = selected_view
    st.session_state[CLAIM_BUCKET_STATE_KEY] = selected_view
    st.session_state[CLAIM_BUCKET_LEGACY_STATE_KEY] = selected_view



def _status_filter_is_user_facing(value: str) -> bool:
    normalized = str(value or "").strip().upper()
    return normalized not in HIDDEN_STATUS_FILTER_VALUES


def _user_facing_status_options(dynamic_options: list[str]) -> list[str]:
    allowed_statuses = {value.upper() for value in STATUS_FILTER_OPTIONS}
    dynamic_visible_statuses = [
        value
        for value in dynamic_options
        if _status_filter_is_user_facing(value)
        and str(value or "").strip().upper() in allowed_statuses
    ]
    return _merge_filter_options(STATUS_FILTER_OPTIONS, dynamic_visible_statuses)


def _prune_hidden_selected_statuses() -> None:
    selected_statuses = _selected_list("selected_statuses")
    visible_statuses = [
        status for status in selected_statuses if _status_filter_is_user_facing(status)
    ]
    if visible_statuses != selected_statuses:
        st.session_state["selected_statuses"] = visible_statuses


def _sync_dashboard_status_filter_state() -> None:
    """Normalize selected status filters before rendering dashboard controls."""
    _prune_hidden_selected_statuses()


def _merge_filter_options(
    default_options: list[str], dynamic_options: list[str]
) -> list[str]:
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

    _sync_dashboard_status_filter_state()
    status_options = _user_facing_status_options(claim_service.get_available_claim_statuses(session))
    claim_type_options = _merge_filter_options(
        [],
        claim_service.get_available_claim_types(session),
    )

    st.markdown(
        "<div class='mfq-dashboard-filter-panel-marker'></div>"
        "<div class='mfq-filter-popover-heading'>Filter Claims</div>",
        unsafe_allow_html=True,
    )
    _render_filter_chip_group(
        "MFQ Status", "selected_statuses", status_options, "status", "All Statuses"
    )
    _render_filter_chip_group(
        "Priority",
        "selected_priorities",
        PRIORITY_FILTER_OPTIONS,
        "priority",
        "All Priorities",
    )
    _render_filter_chip_group(
        "Claim Type",
        "selected_claim_types",
        claim_type_options,
        "claim_type",
        "All Claim Types",
    )
    _render_filter_chip_group(
        "AI Confidence Score",
        "selected_ai_confidence_buckets",
        AI_CONFIDENCE_FILTER_OPTIONS,
        "ai_confidence",
        "All Scores",
    )
    _render_date_requested_filter()
    st.markdown("<div class='mfq-filter-clear-all'></div>", unsafe_allow_html=True)
    safe_button(
        "Clear All Filters",
        key="dashboard_clear_all_filters",
        use_container_width=True,
        on_click=_clear_all_dashboard_filters,
    )


def _render_dashboard_header(session, display_name: str) -> None:
    header_left, header_right = safe_columns([8, 2], vertical_alignment="top")
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
        with safe_container(key="dashboard_header_actions"):
            st.markdown(
                "<div class='dashboard-filter-button-wrapper'>", unsafe_allow_html=True
            )
            active_filter_count = _active_dashboard_filter_count()
            filter_label = (
                f"Filters ({active_filter_count})" if active_filter_count else "Filters"
            )
            with safe_popover(
                filter_label,
                icon=":material/filter_list:",
                width="content",
                key="dashboard_filters_popover",
            ):
                _render_dashboard_filter_controls(session)
            st.markdown("</div>", unsafe_allow_html=True)


def _resolve_user_display_name(ctx) -> str:
    candidate_values = [
        getattr(ctx, "display_name", None),
        getattr(ctx, "full_name", None),
        getattr(ctx, "name", None),
        st.session_state.get("display_name"),
        st.session_state.get("full_name"),
        st.session_state.get("user_full_name"),
        st.session_state.get("username"),
    ]

    user_profile = st.session_state.get("user_profile")
    if isinstance(user_profile, dict):
        candidate_values.extend(
            [
                user_profile.get("display_name"),
                user_profile.get("full_name"),
                user_profile.get("name"),
                user_profile.get("username"),
            ]
        )

    for candidate in candidate_values:
        value = str(candidate or "").strip()
        if value and value.casefold() not in {"none", "null", "nan", "n/a"}:
            return value

    username = str(getattr(ctx, "username", "") or "").strip()
    return (
        username
        if username
        and username.casefold() not in {"none", "null", "nan", "n/a", "unknown"}
        else "User"
    )


def _fallback_filtered_claim_bucket_counts(
    session, shared_filters: dict[str, object]
) -> dict[str, int]:
    """Support older hot-reloaded service modules until Snowflake restarts."""
    return {
        bucket: claim_service.get_filtered_claims_count(
            session,
            _claim_bucket_filters(shared_filters, bucket, _claims_search_text(bucket)),
        )
        for bucket in CLAIM_BUCKET_OPTIONS
    }


def _render_dashboard_view(session, ctx) -> None:
    logger.info("render_dashboard called")
    _init_dashboard_filter_state()
    display_name = _resolve_user_display_name(ctx)

    _render_dashboard_header(session, display_name)

    t0 = perf_counter()
    session_ctx = get_session_context_snapshot(session)
    session_ctx["selected_app_role"] = str(
        st.session_state.get("selected_app_role") or ""
    )
    session_ctx["selected_sf_role"] = str(
        st.session_state.get("selected_sf_role") or ""
    )
    logger.info("dashboard_session_context=%s", session_ctx)
    metrics = get_dashboard_metrics(session, username=ctx.username)
    logger.info("dashboard_metrics_ms=%d", int((perf_counter() - t0) * 1000))
    render_kpi_cards(metrics)

    selected_bucket_for_search = (
        str(st.session_state.get(RECENT_CLAIMS_VIEW_STATE_KEY) or CLAIM_BUCKET_DEFAULT)
        .strip()
        .lower()
    )
    if selected_bucket_for_search not in CLAIM_BUCKET_OPTIONS:
        selected_bucket_for_search = CLAIM_BUCKET_DEFAULT
        st.session_state[RECENT_CLAIMS_VIEW_STATE_KEY] = selected_bucket_for_search
        st.session_state[CLAIM_BUCKET_STATE_KEY] = selected_bucket_for_search
        st.session_state[CLAIM_BUCKET_LEGACY_STATE_KEY] = selected_bucket_for_search
    search_state_key = _claims_search_state_key(selected_bucket_for_search)
    search = _claims_search_text(selected_bucket_for_search)

    with safe_container(key="recent_claims_card"):
        with safe_container(key="recent_claims_toolbar"):
            header_left, header_right = safe_columns([4, 2], vertical_alignment="top")
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
                with safe_container(key="recent_claims_search"):
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
        shared_filters = _dashboard_filters("")
        claim_count_loader = getattr(
            claim_service,
            "get_filtered_claim_bucket_counts",
            _fallback_filtered_claim_bucket_counts,
        )
        claim_counts = claim_count_loader(session, shared_filters)
        for bucket in CLAIM_BUCKET_OPTIONS:
            if not _claims_search_text(bucket).strip():
                claim_counts.setdefault(bucket, 0)

        selected_view = st.session_state.get(
            RECENT_CLAIMS_VIEW_STATE_KEY, CLAIM_BUCKET_DEFAULT
        )
        selected_index = (
            CLAIM_BUCKET_OPTIONS.index(selected_view)
            if selected_view in CLAIM_BUCKET_OPTIONS
            else 0
        )
        radio_kwargs = {
            "horizontal": True,
            "key": RECENT_CLAIMS_VIEW_RADIO_KEY,
            "format_func": lambda bucket: _claim_bucket_label(bucket, claim_counts),
            "label_visibility": "collapsed",
            "on_change": _on_recent_claims_view_change,
        }
        if RECENT_CLAIMS_VIEW_RADIO_KEY not in st.session_state:
            radio_kwargs["index"] = selected_index
        selected_bucket = st.radio(
            "Recent Claims Tabs",
            CLAIM_BUCKET_OPTIONS,
            **radio_kwargs,
        )
        selected_bucket = (
            str(
                st.session_state.get(RECENT_CLAIMS_VIEW_STATE_KEY)
                or selected_bucket
                or CLAIM_BUCKET_DEFAULT
            )
            .strip()
            .lower()
        )
        if selected_bucket not in CLAIM_BUCKET_OPTIONS:
            selected_bucket = CLAIM_BUCKET_DEFAULT
        if selected_bucket != selected_bucket_for_search:
            search = _claims_search_text(selected_bucket)
            filters = _dashboard_filters(search)

        bucket_filters = _claim_bucket_filters(filters, selected_bucket, search)
        all_recent_claims = claim_service.get_cached_recent_claims(session)
        recent_claims = claim_service.get_filtered_recent_claims_local_all(
            all_recent_claims, bucket_filters
        )
        total_claims = len(recent_claims)
        claim_counts[selected_bucket] = total_claims
        st.session_state["dashboard_filtered_claims_count"] = total_claims
        logger.info(
            "dashboard_recent_claims_ms=%d bucket=%s rows=%d total=%d filters=%s",
            int((perf_counter() - t1) * 1000),
            selected_bucket,
            len(recent_claims),
            total_claims,
            bucket_filters,
        )

        dashboard_route_instance = st.session_state.get("dashboard_route_instance", 0)
        render_recent_claims_table(
            df=recent_claims,
            key_prefix="dash",
            empty_message=(
                "No matching claims found"
                if search.strip()
                else (
                    "No recent claims found for the selected filters."
                    if selected_bucket == "recent"
                    else (
                        "No ongoing claims found for the selected filters."
                        if selected_bucket == "ongoing"
                        else "No history claims found for the selected filters."
                    )
                )
            ),
            table_key="recent_claims_table",
            component_key=f"recent_claims_table_{selected_bucket}_{dashboard_route_instance}",
        )


def render(session, ctx) -> None:
    """Render the single active Dashboard implementation once for this router pass."""
    if (
        str(st.session_state.get("current_view") or DASHBOARD_VIEW).strip().lower()
        != DASHBOARD_VIEW
    ):
        return

    _render_dashboard_view(session=session, ctx=ctx)
