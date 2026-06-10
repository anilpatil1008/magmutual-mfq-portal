from __future__ import annotations

import sys
import types
from pathlib import Path

APP_ROOT = Path(__file__).parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# The claim details page imports services that import Snowpark symbols, but
# these action-visibility tests only exercise pure rule helpers.
snowflake_module = types.ModuleType("snowflake")
snowpark_module = types.ModuleType("snowflake.snowpark")
snowpark_module.Session = object
snowflake_module.snowpark = snowpark_module
sys.modules.setdefault("snowflake", snowflake_module)
sys.modules.setdefault("snowflake.snowpark", snowpark_module)

from pages.claim_details import (
    _display_label_for_claim_key,
    _format_display_date,
    _priority_badge_class,
    _priority_from_claim,
    _safe_display,
    _status_badge_class,
    get_claim_action_buttons,
    get_claim_detail_actions,
    normalize_status,
)


def test_normalize_status_is_case_whitespace_and_underscore_safe():
    assert normalize_status(" MFQ_GENERATED ") == "mfq generated"
    assert normalize_status("MFQ   Generated") == "mfq generated"
    assert normalize_status("mfq generated") == "mfq generated"


def test_mfq_generated_shows_assign_and_approve_without_role_check():
    assert get_claim_action_buttons(" mfq generated ") == ["assign_to_faculty", "approve"]
    assert get_claim_action_buttons("MFQ GENERATED") == ["assign_to_faculty", "approve"]
    assert get_claim_action_buttons("MFQ_Generated") == ["assign_to_faculty", "approve"]


def test_rejected_shows_assign_only_without_role_check():
    assert get_claim_action_buttons(" rejected ") == ["assign_to_faculty"]
    assert get_claim_action_buttons("REJECTED") == ["assign_to_faculty"]


def test_approved_hides_actions():
    assert get_claim_action_buttons("approved") == []
    assert get_claim_action_buttons(" APPROVED ") == []


def test_other_statuses_hide_actions():
    assert get_claim_action_buttons("Open") == []
    assert get_claim_action_buttons("Assigned") == []
    assert get_claim_action_buttons(None) == []


def test_claim_status_and_current_role_are_ignored_for_top_card_actions():
    assert get_claim_detail_actions(
        claim_status=" Approved ",
        mfq_status="MFQ GENERATED",
        current_role="role that previously could not act",
    ) == ["assign_to_faculty", "approve"]
    assert get_claim_detail_actions(
        claim_status="Rejected",
        mfq_status="Approved",
        current_role="CLAIM_OPS",
    ) == []
    assert get_claim_detail_actions(
        claim_status="Open",
        mfq_status="Rejected",
        current_role=None,
    ) == ["assign_to_faculty"]


def test_header_badge_helpers_use_mfq_status_and_priority_independently():
    assert _status_badge_class(" MFQ Generated ") == "generated"
    assert _status_badge_class("approved") == "approved"
    assert _status_badge_class("Rejected") == "rejected"
    assert _priority_badge_class(" HIGH ") == "high"
    assert _priority_badge_class("Medium") == "medium"
    assert _priority_badge_class(None) == "default"


def test_priority_display_uses_priority_fields_only_and_displays_unknown_for_missing_values():
    assert _priority_from_claim({"PRIORITY": "High", "MFQ_STATUS": "Rejected"}) == "High"
    assert _priority_from_claim({"PRIORITY": None, "CLAIM_PRIORITY": "medium"}) == "Medium"
    assert _priority_from_claim({"PRIORITY": "N/A", "CLAIM_PRIORITY": "low"}) == "Low"
    assert _priority_from_claim({"PRIORITY": "nan", "MFQ_STATUS": "High"}) == "Unknown"
    assert _priority_from_claim({"PRIORITY": "-", "CLAIM_PRIORITY": " "}) == "Unknown"
    assert _priority_from_claim({"CLAIM_STATUS": "High", "WORKFLOW_STATUS": "Medium"}) == "Unknown"


def test_claim_header_safe_display_labels_and_dates():
    assert _display_label_for_claim_key("FILE_NUMBER") == "FILE NUMBER"
    assert _display_label_for_claim_key("CLAIM_NUMBER") == "FILE NUMBER"
    assert _safe_display(float("nan"), fallback="") == ""
    assert _safe_display(" null ", fallback="") == ""
    assert _format_display_date("2026-01-02 13:45:00") == "Jan 2, 2026"
