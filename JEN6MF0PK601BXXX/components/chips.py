from __future__ import annotations

from core.utils import safe_str


def status_chip(status: str) -> str:
    mapping = {
        "MFQ Generated": "chip chip-blue",
        "Assigned": "chip chip-blue",
        "Approved": "chip chip-green",
        "Rejected": "chip chip-red",
    }
    css = mapping.get(str(status), "chip chip-gray")
    return f'<span class="{css}">{safe_str(status)}</span>'


def priority_chip(priority: str) -> str:
    mapping = {
        "Critical": "chip chip-red",
        "High": "chip chip-yellow",
        "Medium": "chip chip-blue",
        "Low": "chip chip-gray",
    }
    css = mapping.get(str(priority), "chip chip-gray")
    return f'<span class="{css}">{safe_str(priority)}</span>'


def confidence_chip(score) -> str:
    value = float(score or 0)
    if value >= 90:
        css = "chip chip-green"
    elif value >= 80:
        css = "chip chip-yellow"
    else:
        css = "chip chip-red"
    return f'<span class="{css}">{value:.0f}%</span>'
