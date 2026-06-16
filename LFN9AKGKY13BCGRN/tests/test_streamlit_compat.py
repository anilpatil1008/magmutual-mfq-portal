from __future__ import annotations

from types import SimpleNamespace

import pytest

from utils import streamlit_compat


class _Context:
    def __init__(self, events: list[str], name: str, suppress: bool = False):
        self._events = events
        self._name = name
        self._suppress = suppress

    def __enter__(self):
        self._events.append(f"{self._name}:enter")
        return self

    def __exit__(self, exc_type, exc, tb):
        self._events.append(f"{self._name}:exit:{exc_type.__name__ if exc_type else None}")
        return self._suppress


class _BrokenContext:
    def __enter__(self):
        raise TypeError("unsupported popover option")

    def __exit__(self, exc_type, exc, tb):
        return False


def test_safe_popover_falls_back_when_popover_enter_fails(monkeypatch):
    events: list[str] = []

    def _popover(label, **kwargs):
        events.append(f"popover:{label}")
        return _BrokenContext()

    def _expander(label, expanded=False):
        events.append(f"expander:{label}:{expanded}")
        return _Context(events, "expander")

    monkeypatch.setattr(
        streamlit_compat,
        "st",
        SimpleNamespace(popover=_popover, expander=_expander),
    )

    with streamlit_compat.safe_popover("Filters", expanded=True):
        events.append("body")

    assert events == [
        "popover:Filters",
        "expander:Filters:True",
        "expander:enter",
        "body",
        "expander:exit:None",
    ]


def test_safe_popover_propagates_body_exceptions_without_fallback(monkeypatch):
    events: list[str] = []

    def _popover(label, **kwargs):
        events.append(f"popover:{label}")
        return _Context(events, "popover")

    def _expander(label, **kwargs):
        events.append(f"expander:{label}")
        return _Context(events, "expander")

    monkeypatch.setattr(
        streamlit_compat,
        "st",
        SimpleNamespace(popover=_popover, expander=_expander),
    )

    with pytest.raises(ValueError, match="render failed"):
        with streamlit_compat.safe_popover("Filters"):
            events.append("body")
            raise ValueError("render failed")

    assert events == [
        "popover:Filters",
        "popover:enter",
        "body",
        "popover:exit:ValueError",
    ]
