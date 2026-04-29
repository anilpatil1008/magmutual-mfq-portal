from __future__ import annotations

from html import escape

import streamlit as st

from components.badges import render_legend
from components.cards import render_kpi_cards
from components.tables import render_recent_claims_table
from services.claim_service import get_claims_queue
from services.dashboard_service import get_dashboard_metrics


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


def render(session, ctx) -> None:
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

    metrics = get_dashboard_metrics(session, app_role=ctx.app_role, username=ctx.username)
    render_kpi_cards(metrics)
    render_legend()

    card_key = "dash_recent_claims"
    search = st.session_state.get(f"{card_key}_search", "")

    with st.container(key="recent_claims_card"):
        st.markdown("<div class='claims-dashboard-card'>", unsafe_allow_html=True)
        st.markdown("<div class='claims-toolbar'>", unsafe_allow_html=True)
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
            st.markdown("<div class='recent-claims-search'>", unsafe_allow_html=True)
            with st.container(key="recent_claims_search"):
                search = st.text_input(
                    "Search",
                    value=search,
                    placeholder="Search by patient, file #...",
                    label_visibility="collapsed",
                    key=f"{card_key}_search",
                )
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        queue = get_claims_queue(session, ctx.app_role, ctx.username, search_text=search)
        render_recent_claims_table(queue.head(20), key_prefix="dash")
        st.markdown("</div>", unsafe_allow_html=True)
