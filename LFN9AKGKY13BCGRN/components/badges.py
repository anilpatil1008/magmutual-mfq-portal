from __future__ import annotations

from typing import Any

import streamlit as st


STATUS_TO_TONE = {
    "MFQ Generated": "info",
    "Assigned": "warning",
    "On Hold": "muted",
    "Approved": "success",
    "Rejected": "danger",
}


PRIORITY_TO_TONE = {
    "High": "danger",
    "Medium": "warning",
    "Low": "muted",
}


ROLE_TO_TONE = {
    "Admin": "danger",
    "Reviewer": "info",
    "Read Only": "muted",
    "Read-Only": "muted",
    "ReadOnly": "muted",
}

TRUTHY_VALUES = {"true", "yes", "y", "1", "on"}
FALSY_VALUES = {"false", "no", "n", "0", "off"}


def badge_html(label: str, tone: str, badge_type: str, variant: str | None = None) -> str:
    classes = ["mm-badge", f"mm-badge-{tone}", f"mm-badge-{badge_type}"]
    if variant:
        classes.append(f"mm-badge-{badge_type}-{variant}")
    return f"<span class='{' '.join(classes)}'>{label}</span>"


def status_badge(status: str) -> str:
    value = str(status or "Unknown")
    tone = STATUS_TO_TONE.get(value, "muted")
    return badge_html(value, tone, "status")


def priority_badge(priority: str) -> str:
    value = str(priority or "Unknown")
    tone = PRIORITY_TO_TONE.get(value, "muted")
    return badge_html(value, tone, "priority")


def confidence_badge(confidence: Any) -> str:
    if confidence is None:
        return badge_html("N/A", "muted", "confidence", "unknown")

    try:
        score = float(confidence)
    except (TypeError, ValueError):
        return badge_html("N/A", "muted", "confidence", "unknown")

    if 0 <= score <= 1:
        score *= 100
    score = max(0.0, min(score, 100.0))

    if score >= 85:
        tone, band = "success", "high"
    elif score >= 60:
        tone, band = "warning", "medium"
    else:
        tone, band = "danger", "low"

    return badge_html(f"AI Confidence {score:.0f}%", tone, "confidence", band)


def boolean_badge(value: Any, true_label: str = "Yes", false_label: str = "No") -> str:
    if value is None:
        return badge_html("Unknown", "muted", "boolean", "unknown")

    normalized = value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in TRUTHY_VALUES:
            normalized = True
        elif lowered in FALSY_VALUES:
            normalized = False
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if value == 1:
            normalized = True
        elif value == 0:
            normalized = False

    if isinstance(normalized, bool):
        return badge_html(
            true_label if normalized else false_label,
            "success" if normalized else "danger",
            "boolean",
            "true" if normalized else "false",
        )

    return badge_html(str(value), "muted", "boolean", "unknown")


def role_badge(role: str) -> str:
    value = str(role or "Unknown")
    tone = ROLE_TO_TONE.get(value, "muted")
    return badge_html(value, tone, "role")


def render_legend() -> None:
    status_pills = ["MFQ Generated", "Assigned", "On Hold", "Approved", "Rejected"]
    st.markdown(
        (
            "<div class='mm-dashboard-status-pills'>"
            + "".join(
                [f"<span class='mm-dashboard-status-pill'>{status}</span>" for status in status_pills]
            )
            + "</div>"
        ),
        unsafe_allow_html=True,
    )
