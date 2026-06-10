from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

APP_ROOT = Path(__file__).parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from utils import navigation
from components.layout import _sidebar_nav_items


def _patch_session_state(monkeypatch, initial=None):
    session_state = dict(initial or {})
    rerun_calls = {"count": 0}

    def _rerun():
        rerun_calls["count"] += 1

    monkeypatch.setattr(navigation, "st", SimpleNamespace(session_state=session_state, rerun=_rerun))
    session_state["_rerun_calls"] = rerun_calls
    return session_state


def test_navigate_to_dashboard_clears_claim_details_state(monkeypatch):
    state = _patch_session_state(
        monkeypatch,
        {
            "active_page": "Claim Details",
            "current_view": "claim_details",
            "selected_claim_id": "CLM-123",
            "selected_claim": {"CLAIM_ID": "CLM-123"},
            "claim_detail_view": True,
            "show_claim_details_nav": True,
        },
    )

    navigation.navigate_to_dashboard()

    assert state["active_page"] == "Dashboard"
    assert state["current_view"] == "dashboard"
    assert state["claim_scope"] == "ongoing"
    assert state["selected_claim_id"] is None
    assert state["selected_claim"] is None
    assert state["claim_detail_view"] is False
    assert state["show_claim_details_nav"] is False
    assert state["dashboard_route_instance"] == 1
    assert state["_rerun_calls"]["count"] == 1


def test_navigate_to_claim_details_sets_single_claim_details_route(monkeypatch):
    state = _patch_session_state(monkeypatch)

    navigation.navigate_to_claim_details(" CLM-456 ")

    assert state["selected_claim_id"] == "CLM-456"
    assert state["active_page"] == "Claim Details"
    assert state["current_view"] == "claim_details"
    assert state["claim_detail_view"] is True
    assert state["show_claim_details_nav"] is True
    assert navigation.is_claim_details_route_active() is True
    assert state["_rerun_calls"]["count"] == 1


def test_stale_selected_claim_does_not_route_without_claim_details_view(monkeypatch):
    _patch_session_state(
        monkeypatch,
        {
            "current_view": "dashboard",
            "selected_claim_id": "CLM-789",
        },
    )

    assert navigation.is_claim_details_route_active() is False


def test_navigate_to_reports_clears_selected_claim(monkeypatch):
    state = _patch_session_state(
        monkeypatch,
        {
            "current_view": "claim_details",
            "active_page": "Claim Details",
            "selected_claim_id": "CLM-789",
            "selected_claim": {"CLAIM_ID": "CLM-789"},
            "claim_detail_view": True,
            "show_claim_details_nav": True,
        },
    )

    navigation.navigate_to_reports()

    assert state["active_page"] == "Reports"
    assert state["current_view"] == "reports"
    assert state["selected_claim_id"] is None
    assert state["selected_claim"] is None
    assert state["claim_detail_view"] is False
    assert state["show_claim_details_nav"] is False
    assert state["_rerun_calls"]["count"] == 1


def test_dashboard_route_instance_advances_only_when_reentering_dashboard(monkeypatch):
    state = _patch_session_state(
        monkeypatch,
        {
            "current_view": "claim_details",
            "active_page": "Claim Details",
            "selected_claim_id": "CLM-123",
            "dashboard_route_instance": 2,
        },
    )

    navigation.set_dashboard_route()

    assert state["dashboard_route_instance"] == 3
    assert state["claim_scope"] == "ongoing"

    state["claim_scope"] = "history"
    navigation.set_dashboard_route()

    assert state["dashboard_route_instance"] == 3
    assert state["claim_scope"] == "ongoing"


def test_dashboard_route_instance_is_not_advanced_during_dashboard_normalization(monkeypatch):
    state = _patch_session_state(
        monkeypatch,
        {
            "current_view": "dashboard",
            "active_page": "Dashboard",
            "selected_claim_id": None,
            "dashboard_route_instance": 7,
        },
    )

    navigation.set_dashboard_route()

    assert state["dashboard_route_instance"] == 7


def _sidebar_labels_and_active(current_view, selected_claim_id=None):
    return [
        (label, active)
        for label, _view, _navigate, active in _sidebar_nav_items(
            current_view,
            selected_claim_id or "",
        )
    ]


def test_sidebar_defaults_to_dashboard_and_reports_only():
    assert _sidebar_labels_and_active("dashboard") == [
        ("Dashboard", True),
        ("Reports", False),
    ]


def test_sidebar_shows_active_claim_details_only_for_selected_claim_route():
    assert _sidebar_labels_and_active("claim_details", "CLM-123") == [
        ("Dashboard", False),
        ("Claim Details", True),
        ("Reports", False),
    ]


def test_sidebar_hides_claim_details_when_claim_id_is_missing():
    assert _sidebar_labels_and_active("claim_details") == [
        ("Dashboard", False),
        ("Reports", False),
    ]


def test_sidebar_reports_active_without_claim_details():
    assert _sidebar_labels_and_active("reports", "CLM-123") == [
        ("Dashboard", False),
        ("Reports", True),
    ]
