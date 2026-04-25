from __future__ import annotations

import streamlit as st


STATUS_TO_CLASS = {
    "MFQ Generated": "info",
    "Assigned": "warning",
    "Approved": "success",
    "Rejected": "danger",
}


PRIORITY_TO_CLASS = {
    "High": "danger",
    "Medium": "warning",
    "Low": "muted",
}


def badge_html(label: str, tone: str) -> str:
    return f"<span class='mm-badge mm-badge-{tone}'>{label}</span>"


def status_badge(status: str) -> str:
    return badge_html(status, STATUS_TO_CLASS.get(status, "muted"))


def priority_badge(priority: str) -> str:
    return badge_html(priority, PRIORITY_TO_CLASS.get(priority, "muted"))


def render_legend() -> None:
    st.markdown(
        " ".join(
            [
                status_badge("MFQ Generated"),
                status_badge("Assigned"),
                status_badge("Approved"),
                status_badge("Rejected"),
            ]
        ),
        unsafe_allow_html=True,
    )
