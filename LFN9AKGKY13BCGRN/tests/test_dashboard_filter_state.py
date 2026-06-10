from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace

APP_ROOT = Path(__file__).parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# Dashboard imports the claim service, which imports Snowpark at module import
# time. These session-state tests do not need a live Snowflake dependency.
snowflake_module = types.ModuleType("snowflake")
snowpark_module = types.ModuleType("snowflake.snowpark")
snowpark_module.Session = object
snowflake_module.snowpark = snowpark_module
sys.modules.setdefault("snowflake", snowflake_module)
sys.modules.setdefault("snowflake.snowpark", snowpark_module)

from pages import dashboard


def test_clear_dashboard_filters_resets_recent_claims_view_and_search(monkeypatch):
    session_state = {
        "selected_statuses": ["Assigned"],
        "selected_priorities": ["High"],
        "selected_ai_confidence_buckets": ["Low"],
        "selected_claim_types": ["Professional Liability"],
        "date_requested_from": object(),
        "date_requested_to": object(),
        "date_requested_widget_version": 2,
        "claims_page_number": 4,
        "dash_recent_claims_pagination_page": 4,
        "dash_recent_claims_search": "smith",
        "dash_ongoing_claims_search": "jones",
        "dash_history_claims_search": "approved",
        "selected_claim_view": "history",
        "claim_scope": "history",
    }
    monkeypatch.setattr(dashboard, "st", SimpleNamespace(session_state=session_state))

    dashboard._clear_all_dashboard_filters_before_widgets()

    assert session_state["selected_statuses"] == []
    assert session_state["selected_priorities"] == []
    assert session_state["selected_ai_confidence_buckets"] == []
    assert session_state["selected_claim_types"] == []
    assert session_state["date_requested_from"] is None
    assert session_state["date_requested_to"] is None
    assert session_state["claims_page_number"] == 1
    assert session_state["dash_recent_claims_pagination_page"] == 1
    assert session_state["dash_recent_claims_search"] == ""
    assert session_state["dash_ongoing_claims_search"] == ""
    assert session_state["dash_history_claims_search"] == ""
    assert session_state["recent_claims_view"] == "ongoing"
    assert session_state["recent_claims_view_radio"] == "ongoing"
    assert session_state["selected_claim_view"] == "ongoing"
    assert session_state["claim_scope"] == "ongoing"
    assert session_state["date_requested_widget_version"] == 3


def test_dashboard_filter_state_migrates_legacy_claim_scope(monkeypatch):
    session_state = {"claim_scope": "history"}
    monkeypatch.setattr(dashboard, "st", SimpleNamespace(session_state=session_state))

    dashboard._init_dashboard_filter_state()

    assert session_state["selected_claim_view"] == "history"
    assert session_state["claim_scope"] == "history"


def test_recent_claim_view_does_not_apply_bucket_filter():
    filters = dashboard._claim_bucket_filters({"search_text": ""}, "recent", "smith")

    assert filters == {"search_text": "smith"}


def test_history_claim_view_applies_history_bucket_filter():
    filters = dashboard._claim_bucket_filters({"search_text": ""}, "history", "approved")

    assert filters == {"search_text": "approved", "claim_bucket": "history"}


def test_recent_claims_view_callback_syncs_radio_aliases_and_resets_pagination(monkeypatch):
    session_state = {
        "recent_claims_view": "ongoing",
        "recent_claims_view_radio": "history",
        "selected_claim_view": "ongoing",
        "claim_scope": "ongoing",
        "claims_page_number": 3,
        "dash_recent_claims_pagination_page": 3,
    }
    monkeypatch.setattr(dashboard, "st", SimpleNamespace(session_state=session_state))

    dashboard._on_recent_claims_view_change()

    assert session_state["recent_claims_view"] == "history"
    assert session_state["selected_claim_view"] == "history"
    assert session_state["claim_scope"] == "history"
    assert session_state["claims_page_number"] == 1
    assert session_state["dash_recent_claims_pagination_page"] == 1


def test_dashboard_filter_state_keeps_radio_key_in_sync_with_recent_claim_view(monkeypatch):
    session_state = {"recent_claims_view": "history", "recent_claims_view_radio": "ongoing"}
    monkeypatch.setattr(dashboard, "st", SimpleNamespace(session_state=session_state))

    dashboard._init_dashboard_filter_state()

    assert session_state["recent_claims_view"] == "history"
    assert session_state["recent_claims_view_radio"] == "history"
    assert session_state["selected_claim_view"] == "history"
    assert session_state["claim_scope"] == "history"


def test_dashboard_imports_when_navigation_claim_view_constants_are_missing(monkeypatch):
    import importlib.util
    import types

    def _module(name, **attrs):
        module = types.ModuleType(name)
        for attr_name, attr_value in attrs.items():
            setattr(module, attr_name, attr_value)
        return module

    monkeypatch.setitem(sys.modules, "streamlit", _module("streamlit", session_state={}))
    monkeypatch.setitem(sys.modules, "components", _module("components"))
    monkeypatch.setitem(
        sys.modules,
        "components.cards",
        _module("components.cards", render_kpi_cards=lambda *args, **kwargs: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "components.tables",
        _module(
            "components.tables",
            render_live_claims_search=lambda *args, **kwargs: None,
            render_recent_claims_table=lambda *args, **kwargs: None,
        ),
    )
    monkeypatch.setitem(sys.modules, "services", _module("services"))
    monkeypatch.setitem(
        sys.modules,
        "services.claim_service",
        _module(
            "services.claim_service",
            get_available_claim_statuses=lambda *args, **kwargs: [],
            get_available_claim_types=lambda *args, **kwargs: [],
            get_filtered_claims_count=lambda *args, **kwargs: 0,
            get_filtered_recent_claims=lambda *args, **kwargs: [],
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "services.dashboard_service",
        _module("services.dashboard_service", get_dashboard_metrics=lambda *args, **kwargs: {}),
    )
    monkeypatch.setitem(
        sys.modules,
        "services.rbac_service",
        _module("services.rbac_service", get_session_context_snapshot=lambda *args, **kwargs: {}),
    )
    older_navigation = _module("utils.navigation", DASHBOARD_VIEW="dashboard")
    utils_module = _module("utils", navigation=older_navigation)
    monkeypatch.setitem(sys.modules, "utils", utils_module)
    monkeypatch.setitem(sys.modules, "utils.navigation", older_navigation)

    spec = importlib.util.spec_from_file_location(
        "dashboard_with_older_navigation",
        APP_ROOT / "pages" / "dashboard.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert module.CLAIM_BUCKET_OPTIONS == ("recent", "ongoing", "history")
    assert module.CLAIM_BUCKET_DEFAULT == "ongoing"
    assert module.CLAIM_BUCKET_STATE_KEY == "selected_claim_view"
    assert module.CLAIM_BUCKET_LEGACY_STATE_KEY == "claim_scope"
