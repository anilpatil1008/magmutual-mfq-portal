from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

APP_ROOT = Path(__file__).parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from utils import navigation


def _patch_session_state(monkeypatch, initial=None):
    session_state = dict(initial or {})
    monkeypatch.setattr(navigation, "st", SimpleNamespace(session_state=session_state))
    return session_state


def test_navigate_to_dashboard_clears_claim_details_state(monkeypatch):
    state = _patch_session_state(
        monkeypatch,
        {
            "active_page": "Claim Details",
            "current_view": "claim_details",
            "active_sidebar_item": "Claim Details",
            "selected_claim_id": "CLM-123",
            "selected_claim": {"CLAIM_ID": "CLM-123"},
            "claim_detail_view": True,
            "show_claim_details_nav": True,
        },
    )

    navigation.navigate_to_dashboard()

    assert state["active_page"] == "Dashboard"
    assert state["current_view"] == "dashboard"
    assert state["active_sidebar_item"] == "Dashboard"
    assert state["selected_claim_id"] is None
    assert state["selected_claim"] is None
    assert state["claim_detail_view"] is False
    assert state["show_claim_details_nav"] is False
    assert navigation.should_show_claim_details_nav() is False


def test_navigate_to_claim_details_sets_single_claim_details_route(monkeypatch):
    state = _patch_session_state(monkeypatch)

    navigation.navigate_to_claim_details(" CLM-456 ")

    assert state["selected_claim_id"] == "CLM-456"
    assert state["active_page"] == "Claim Details"
    assert state["current_view"] == "claim_details"
    assert state["active_sidebar_item"] == "Claim Details"
    assert state["claim_detail_view"] is True
    assert state["show_claim_details_nav"] is True
    assert navigation.is_claim_details_route_active() is True
    assert navigation.should_show_claim_details_nav() is True


def test_claim_details_nav_stays_hidden_for_stale_selected_claim(monkeypatch):
    _patch_session_state(
        monkeypatch,
        {
            "current_view": "dashboard",
            "selected_claim_id": "CLM-789",
            "show_claim_details_nav": True,
        },
    )

    assert navigation.is_claim_details_route_active() is False
    assert navigation.should_show_claim_details_nav() is False
