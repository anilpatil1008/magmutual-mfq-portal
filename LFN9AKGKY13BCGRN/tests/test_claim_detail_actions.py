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

import streamlit as st

for dialog_api_name in ("dialog", "experimental_dialog"):
    if hasattr(st, dialog_api_name):
        delattr(st, dialog_api_name)

import pages.claim_details as claim_details
from pages.claim_details import (
    _claim_meta_items,
    _claim_title,
    _display_label_for_claim_key,
    _format_display_date,
    _mfq_status_from_claim,
    _priority_badge_class,
    _priority_from_claim,
    _safe_display,
    _status_badge_class,
    display_value,
    format_unknown,
    get_claim_action_buttons,
    get_claim_detail_actions,
    normalize_status,
)


def test_claim_details_imports_without_streamlit_dialog_apis():
    assert not hasattr(st, "dialog")
    assert not hasattr(st, "experimental_dialog")


def test_back_to_dashboard_callback_updates_route_without_forcing_rerun(monkeypatch):
    calls = {
        "set_dashboard_route": 0,
        "clear_query_params": 0,
        "navigate_to_dashboard": 0,
    }

    class QueryParams:
        def clear(self):
            calls["clear_query_params"] += 1

    monkeypatch.setattr(claim_details.st, "query_params", QueryParams(), raising=False)
    monkeypatch.setattr(
        claim_details,
        "set_dashboard_route",
        lambda: calls.__setitem__(
            "set_dashboard_route", calls["set_dashboard_route"] + 1
        ),
    )
    monkeypatch.setattr(
        claim_details,
        "navigate_to_dashboard",
        lambda: calls.__setitem__(
            "navigate_to_dashboard", calls["navigate_to_dashboard"] + 1
        ),
    )

    claim_details._go_back_to_dashboard()

    assert calls == {
        "set_dashboard_route": 1,
        "clear_query_params": 1,
        "navigate_to_dashboard": 0,
    }


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


def test_claim_header_meta_items_show_only_first_row_fields_with_unknown_specialty():
    meta_items = _claim_meta_items(
        "CLM-123",
        {
            "CLAIM_ID": "CLM-123",
            "Defendant Specialty": "-",
            "DATE_REQUESTED": "2026-01-02",
            "MAGMUTUAL_CONTACT": "Alex Reviewer",
            "CONTACT_EMAIL": "alex@example.com",
            "MFQ_STATUS": "Rejected",
            "PRIORITY": "High",
        },
    )

    assert meta_items == [
        ("FILE_NUMBER", "CLM-123"),
        ("DEFENDANT_SPECIALTY", "Unknown"),
        ("DATE_REQUESTED", "Jan 2, 2026"),
        ("MAGMUTUAL_CONTACT", "Alex Reviewer"),
        ("CONTACT_EMAIL", "alex@example.com"),
    ]
    assert "MFQ_STATUS" not in dict(meta_items)
    assert "PRIORITY" not in dict(meta_items)


def test_claim_title_always_uses_patient_vs_defendant_with_unknown_fallbacks():
    assert (
        _claim_title(
            {"PATIENT_NAME": "Patient Name", "DEFENDANT_NAME": "Defendant Name"}
        )
        == "Patient Name vs Defendant Name"
    )
    assert (
        _claim_title({"PATIENT_NAME": "Patient Name", "DEFENDANT_NAME": None})
        == "Patient Name vs Unknown"
    )
    assert (
        _claim_title({"CLAIMANT_NAME": "AMSURG, LLC", "DEFENDANT_NAME": "-"})
        == "AMSURG, LLC vs Unknown"
    )
    assert (
        _claim_title({"PATIENT_DEFENDANT": "Legacy Patient / Legacy Defendant"})
        == "Legacy Patient vs Legacy Defendant"
    )
    assert _claim_title({}) == "Unknown vs Unknown"


def test_format_unknown_uses_unknown_for_required_header_values():
    assert format_unknown(None) == "Unknown"
    assert format_unknown(float("nan")) == "Unknown"
    assert format_unknown("") == "Unknown"
    assert format_unknown("-") == "Unknown"
    assert format_unknown("AMSURG, LLC") == "AMSURG, LLC"


def test_display_value_uses_unknown_for_claim_header_null_like_values():
    assert display_value(None) == "Unknown"
    assert display_value(float("nan")) == "Unknown"
    assert display_value("") == "Unknown"
    assert display_value(" ") == "Unknown"
    assert display_value("-") == "Unknown"
    assert display_value("Assigned") == "Assigned"


def test_mfq_status_helper_supports_human_readable_column_name_and_unknown_fallback():
    assert _mfq_status_from_claim({"MFQ Status": "Approved"}) == "Approved"
    assert display_value(_mfq_status_from_claim({"MFQ_STATUS": "-"})) == "Unknown"
    assert display_value(_mfq_status_from_claim({})) == "Unknown"
