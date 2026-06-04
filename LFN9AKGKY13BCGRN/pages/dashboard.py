from __future__ import annotations

from html import escape
import logging
from time import perf_counter

import streamlit as st

from components.cards import render_kpi_cards
from components.tables import render_recent_claims_table
from pages import claim_details
from services.claim_service import (
    get_available_claim_statuses,
    get_filtered_claims_count,
    get_filtered_recent_claims,
)
from services.dashboard_service import get_dashboard_metrics
from services.rbac_service import get_session_context_snapshot

logger = logging.getLogger(__name__)

DASHBOARD_RECENT_CLAIMS_PAGE_SIZE = 10
STATUS_FILTER_OPTIONS = ["All Statuses", "MFQ Generated", "Assigned", "Approved", "Rejected"]
PRIORITY_FILTER_OPTIONS = ["All Priorities", "High", "Medium", "Low"]
AI_CONFIDENCE_FILTER_OPTIONS = [
    ("All Scores", "All Scores"),
    ("High", "High (90%+)"),
    ("Medium", "Medium (80-89%)"),
    ("Low", "Low (<80%)"),
]


def _init_dashboard_filter_state() -> None:
    defaults = {
        "selected_status": "All Statuses",
        "selected_priority": "All Priorities",
        "selected_ai_confidence": "All Scores",
        "claims_page_number": 1,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _filter_button_slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value)).strip("_")


def _set_dashboard_filter(state_key: str, value: str) -> None:
    if st.session_state.get(state_key) != value:
        st.session_state[state_key] = value
        st.session_state["claims_page_number"] = 1
        st.session_state["dash_recent_claims_pagination_page"] = 1
        st.rerun()


def _render_filter_chip_group(title: str, state_key: str, options: list[str] | list[tuple[str, str]], group_key: str) -> None:
    st.markdown(f"<p class='mfq-filter-section-label'>{escape(title)}</p>", unsafe_allow_html=True)
    columns = st.columns(3, gap="small")
    for index, option in enumerate(options):
        value, label = option if isinstance(option, tuple) else (option, option)
        selected = st.session_state.get(state_key) == value
        state_suffix = "selected" if selected else "unselected"
        chip_key = f"filter_chip_{group_key}_{_filter_button_slug(str(value))}_{state_suffix}"
        with columns[index % 3]:
            with st.container(key=chip_key):
                if st.button(str(label), key=f"{chip_key}_button", use_container_width=True):
                    _set_dashboard_filter(state_key, str(value))


def _dashboard_filters() -> dict[str, str]:
    return {
        "selected_status": str(st.session_state.get("selected_status") or "All Statuses"),
        "selected_priority": str(st.session_state.get("selected_priority") or "All Priorities"),
        "selected_ai_confidence": str(st.session_state.get("selected_ai_confidence") or "All Scores"),
        "search_text": str(st.session_state.get("dash_recent_claims_search") or ""),
    }


def _render_dashboard_filter_controls(session) -> None:
    available_statuses = {status.upper() for status in get_available_claim_statuses(session)}
    status_options = [*STATUS_FILTER_OPTIONS]
    if "ON HOLD" in available_statuses:
        status_options.append("On Hold")

    st.markdown("<div class='mfq-filter-popover-heading'>Filter Claims</div>", unsafe_allow_html=True)
    _render_filter_chip_group("Status", "selected_status", status_options, "status")
    _render_filter_chip_group("Priority", "selected_priority", PRIORITY_FILTER_OPTIONS, "priority")
    _render_filter_chip_group("AI Confidence Score", "selected_ai_confidence", AI_CONFIDENCE_FILTER_OPTIONS, "ai_confidence")


def _render_dashboard_header(session, display_name: str) -> None:
    header_left, header_right = st.columns([5, 2], vertical_alignment="center")
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
            filter_col, report_col = st.columns([1, 1.35], gap="small", vertical_alignment="center")
            with filter_col:
                if hasattr(st, "popover"):
                    with st.popover("Filters"):
                        _render_dashboard_filter_controls(session)
                else:
                    with st.expander("Filters", expanded=False):
                        _render_dashboard_filter_controls(session)
            with report_col:
                st.button("Generate Report", key="dashboard_generate_report", type="primary", use_container_width=True)



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

    if st.session_state.get("current_view") == "dashboard":
        _render_dashboard_view(session=session, ctx=ctx)
        st.stop()

    # Fallback to dashboard when state is unknown.
    st.session_state["current_view"] = "dashboard"
    _render_dashboard_view(session=session, ctx=ctx)
    st.stop()
