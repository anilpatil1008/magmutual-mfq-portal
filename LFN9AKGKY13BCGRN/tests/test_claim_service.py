from __future__ import annotations

import sys
import types
from pathlib import Path

import pandas as pd

APP_ROOT = Path(__file__).parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# The unit under test imports the Snowpark Session type at module import time,
# but these queue-shaping tests do not need a live Snowflake dependency.
snowflake_module = types.ModuleType("snowflake")
snowpark_module = types.ModuleType("snowflake.snowpark")
snowpark_module.Session = object
snowflake_module.snowpark = snowpark_module
sys.modules.setdefault("snowflake", snowflake_module)
sys.modules.setdefault("snowflake.snowpark", snowpark_module)

from services import claim_service


def test_get_claims_queue_sorts_by_date_requested_without_last_updated(monkeypatch):
    queue = pd.DataFrame(
        [
            {"CLAIM_ID": "CLM-1", "CLAIM_STATUS": "Assigned", "DATE_REQUESTED": "2026-01-01"},
            {"CLAIM_ID": "CLM-2", "CLAIM_STATUS": "Assigned", "DATE_REQUESTED": "2026-03-01"},
        ]
    )
    monkeypatch.setattr(claim_service.claims_repository, "get_claims_queue", lambda session: queue)

    result = claim_service.get_claims_queue(session=object(), username="apatil")

    assert result["CLAIM_ID"].tolist() == ["CLM-2", "CLM-1"]


def test_get_claims_queue_falls_back_to_last_updated_when_date_requested_missing(monkeypatch):
    queue = pd.DataFrame(
        [
            {"CLAIM_ID": "CLM-1", "LAST_UPDATED_TS": "2026-01-01"},
            {"CLAIM_ID": "CLM-2", "LAST_UPDATED_TS": "2026-03-01"},
        ]
    )
    monkeypatch.setattr(claim_service.claims_repository, "get_claims_queue", lambda session: queue)

    result = claim_service.get_claims_queue(session=object(), username="apatil")

    assert result["CLAIM_ID"].tolist() == ["CLM-2", "CLM-1"]


def test_get_claims_queue_returns_unsorted_when_recency_columns_missing(monkeypatch):
    queue = pd.DataFrame(
        [
            {"CLAIM_ID": "CLM-1", "CLAIM_STATUS": "Assigned"},
            {"CLAIM_ID": "CLM-2", "CLAIM_STATUS": "Assigned"},
        ]
    )
    monkeypatch.setattr(claim_service.claims_repository, "get_claims_queue", lambda session: queue)

    result = claim_service.get_claims_queue(session=object(), username="apatil")

    assert result["CLAIM_ID"].tolist() == ["CLM-1", "CLM-2"]


def test_dashboard_claim_search_where_clause_includes_live_search_columns():
    where_clause, params = claim_service.build_claim_filter_where_clause({"search_text": "smith"})

    for column in (
        "CLAIM_ID",
        "FILE_NUMBER",
        "PATIENT_DEFENDANT",
        "DEFENDANT_NAME",
        "MFQ_STATUS",
        "WORKFLOW_STATUS",
        "PRIORITY",
        "CLAIM_TYPE",
        "CLAIM_STATUS",
    ):
        assert f"TO_VARCHAR({column}) ILIKE ?" in where_clause
    assert params == ["%smith%"] * 9
