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

from pages.claim_details import get_claim_detail_actions


def test_mfq_generated_claim_ops_sees_assign_and_approve_with_role_underscores():
    assert get_claim_detail_actions(
        claim_status="Open",
        mfq_status=" mfq generated ",
        current_role="CLAIM_OPS",
    ) == ["assign_to_faculty", "approve"]


def test_approved_mfq_status_hides_actions_for_any_role():
    assert get_claim_detail_actions(
        claim_status="Open",
        mfq_status="approved",
        current_role="CLAIM_ANALYST_SUPERVISOR",
    ) == []


def test_claim_status_does_not_override_mfq_status_for_actions():
    assert get_claim_detail_actions(
        claim_status=" Approved ",
        mfq_status="MFQ GENERATED",
        current_role="CLAIM_OPS",
    ) == ["assign_to_faculty", "approve"]
    assert get_claim_detail_actions(
        claim_status="Rejected",
        mfq_status="Approved",
        current_role="CLAIM_OPS",
    ) == []


def test_rejected_claim_ops_and_supervisor_see_assign_only():
    assert get_claim_detail_actions(
        claim_status="Open",
        mfq_status=" rejected ",
        current_role="Claim Ops",
    ) == ["assign_to_faculty"]
    assert get_claim_detail_actions(
        claim_status="Open",
        mfq_status="REJECTED",
        current_role="CLAIM_ANALYST_SUPERVISOR",
    ) == ["assign_to_faculty"]


def test_rejected_other_role_sees_no_actions():
    assert get_claim_detail_actions(
        claim_status="Open",
        mfq_status="Rejected",
        current_role="CLAIM_ANALYST",
    ) == []


def test_claims_analyst_and_accountadmin_can_act_on_generated_claim():
    assert get_claim_detail_actions(
        claim_status="Open",
        mfq_status="MFQ Generated",
        current_role="Claims Analyst",
    ) == ["assign_to_faculty", "approve"]
    assert get_claim_detail_actions(
        claim_status="Open",
        mfq_status="MFQ Generated",
        current_role="ACCOUNTADMIN",
    ) == ["assign_to_faculty", "approve"]
