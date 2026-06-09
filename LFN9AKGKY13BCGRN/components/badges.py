from __future__ import annotations

import re
from html import escape
from typing import Any

import pandas as pd


STATUS_TO_TONE = {
    "MFQ Generated": "info",
    "Assigned": "info",
    "On Hold": "warning",
    "Approved": "success",
    "Rejected": "danger",
}


PRIORITY_TO_TONE = {
    "Critical": "danger",
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
NULL_DISPLAY_VALUES = {"", "nan", "none", "null", "n/a", "na"}
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}


def safe_display(value: Any, fallback: str = "-") -> str:
    """Return display-safe text, suppressing None/NaN/null-like values."""
    if value is None:
        return fallback
    try:
        if pd.isna(value):
            return fallback
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if text.casefold() in NULL_DISPLAY_VALUES:
        return fallback
    return text


def get_case_insensitive_value(data: dict[str, Any], *keys: str, fallback: Any = None) -> Any:
    """Read the first present key from a dict, matching Snowflake column casing safely."""
    if not isinstance(data, dict):
        return fallback
    lookup = {str(key).casefold(): key for key in data.keys()}
    for key in keys:
        actual_key = lookup.get(str(key).casefold())
        if actual_key is not None:
            value = data.get(actual_key)
            if safe_display(value, fallback=""):
                return value
    return fallback


def normalize_badge_value(value: Any) -> str:
    """Normalize values for badge comparisons across case, spaces, and underscores."""
    text = safe_display(value, fallback="")
    return re.sub(r"[\s_]+", " ", text).strip().casefold()


def format_status_label(status: Any) -> str:
    text = safe_display(status)
    if text == "-":
        return "-"
    normalized = normalize_badge_value(text)
    labels = {
        "mfq generated": "MFQ Generated",
        "intake complete": "Intake Complete",
        "ready for embedding": "Ready For Embedding",
        "synced": "Synced",
        "approved": "Approved",
        "rejected": "Rejected",
        "on hold": "On Hold",
        "insufficient": "Insufficient",
        "assigned": "Assigned",
    }
    return labels.get(normalized, text.replace("_", " ").title() if "_" in text else text)


def get_status_badge_class(status: Any) -> str:
    """Return the shared MFQ status CSS class with case-insensitive mapping."""
    normalized = normalize_badge_value(status)
    if normalized == "mfq generated":
        return "status-mfq-generated"
    if normalized == "intake complete":
        return "status-intake-complete"
    if normalized == "ready for embedding":
        return "status-ready-for-embedding"
    if normalized == "synced":
        return "status-synced"
    if normalized == "approved":
        return "status-approved"
    if normalized == "rejected":
        return "status-rejected"
    if normalized == "on hold":
        return "status-on-hold"
    if normalized == "insufficient":
        return "status-insufficient"
    if normalized == "assigned":
        return "status-assigned"
    return "status-default"


def get_priority_badge_class(priority: Any) -> str:
    """Return the shared priority CSS class with case-insensitive mapping."""
    normalized = normalize_badge_value(priority)
    if normalized == "critical":
        return "priority-critical"
    if normalized == "high":
        return "priority-high"
    if normalized == "medium":
        return "priority-medium"
    if normalized == "low":
        return "priority-low"
    return "priority-default"


def format_priority_label(priority: Any) -> str:
    text = safe_display(priority)
    if text == "-":
        return "-"
    normalized = normalize_badge_value(text)
    labels = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low"}
    return labels.get(normalized, text.replace("_", " ").title() if "_" in text else text)


def badge_html(label: str, tone: str, badge_type: str, variant: str | None = None) -> str:
    classes = ["mm-badge", f"mm-badge-{tone}", f"mm-badge-{badge_type}"]
    if variant:
        classes.append(f"mm-badge-{badge_type}-{variant}")
    return f"<span class='{' '.join(classes)}'>{escape(safe_display(label))}</span>"


def render_status_badge(status: Any) -> str:
    label = format_status_label(status)
    raw_title = safe_display(status, fallback="-")
    return f"<span class='status-badge {get_status_badge_class(status)}' title='{escape(raw_title)}'>{escape(label)}</span>"


def render_priority_badge(priority: Any) -> str:
    label = format_priority_label(priority)
    raw_title = safe_display(priority, fallback="-")
    return f"<span class='priority-badge {get_priority_badge_class(priority)}' title='{escape(raw_title)}'>{escape(label)}</span>"


def status_badge(status: str) -> str:
    return render_status_badge(status)


def priority_badge(priority: str) -> str:
    return render_priority_badge(priority)


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
    value = safe_display(role, fallback="Unknown")
    tone = ROLE_TO_TONE.get(value, "muted")
    return badge_html(value, tone, "role")
