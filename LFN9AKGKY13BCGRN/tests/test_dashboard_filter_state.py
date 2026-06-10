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
    assert session_state["claim_scope"] == "ongoing"
    assert session_state["date_requested_widget_version"] == 3
