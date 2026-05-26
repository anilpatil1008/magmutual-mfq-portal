from __future__ import annotations

from html import escape
import logging
from time import perf_counter

import streamlit as st

from components.badges import render_legend
from components.cards import render_kpi_cards
from components.tables import filter_recent_claims_by_search, render_recent_claims_table
from pages import claim_details
from services.claim_service import get_claims_queue
from services.dashboard_service import get_dashboard_metrics
from utils.claim_lifecycle import classify_claim_bucket

logger = logging.getLogger(__name__)


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
    st.title("Dashboard")
    display_name = _resolve_user_display_name(ctx)
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

    t0 = perf_counter()
    metrics = get_dashboard_metrics(session, app_role=ctx.app_role, username=ctx.username)
    logger.info("dashboard_metrics_ms=%d", int((perf_counter() - t0) * 1000))
    render_kpi_cards(metrics)
    render_legend()

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


        t1 = perf_counter()
        queue = get_claims_queue(session, ctx.app_role, ctx.username)
        logger.info("dashboard_recent_claims_ms=%d rows=%d", int((perf_counter() - t1) * 1000), len(queue))
        if queue.empty:
            render_recent_claims_table(queue, key_prefix="dash")
            return

        queue = queue.copy()
        queue["CLAIM_BUCKET"] = queue.apply(classify_claim_bucket, axis=1)
        ongoing_df = queue[queue["CLAIM_BUCKET"] == "ongoing"]
        history_df = queue[queue["CLAIM_BUCKET"] == "history"]

        selected_tab = st.radio(
            "Recent Claims Tabs",
            [f"Ongoing Claims ({len(ongoing_df)})", f"History Claims ({len(history_df)})"],
            horizontal=True,
            key=f"{card_key}_tab",
            label_visibility="collapsed",
        )
        previous_tab = st.session_state.get(f"{card_key}_prev_tab")
        previous_search = st.session_state.get(f"{card_key}_prev_search", "")
        if previous_tab != selected_tab or str(previous_search) != str(search):
            st.session_state["dash_recent_claims_pagination_page"] = 1
        st.session_state[f"{card_key}_prev_tab"] = selected_tab
        st.session_state[f"{card_key}_prev_search"] = search

        tab_df = ongoing_df if selected_tab.startswith("Ongoing") else history_df
        tab_df = filter_recent_claims_by_search(tab_df, search)

        logger.info("render_recent_claims called tab=%s rows=%d", selected_tab, len(tab_df))
        render_recent_claims_table(
            tab_df,
            key_prefix="dash",
            empty_message="No ongoing claims found." if selected_tab.startswith("Ongoing") else "No history claims found.",
        )


def render(session, ctx) -> None:
    if "current_view" not in st.session_state:
        st.session_state["current_view"] = "dashboard"

    if st.session_state.get("current_view") == "claim_details" and st.session_state.get("selected_claim_id"):
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
