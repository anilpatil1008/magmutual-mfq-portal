from __future__ import annotations

import math
import sys
from pathlib import Path

APP_ROOT = Path(__file__).parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import pandas as pd

from services import rbac_service
from services.rbac_service import can_edit_claim


def test_can_edit_claim_handles_nan_assignment_without_crashing():
    assert not can_edit_claim("Assigned", math.nan, "APatil")


def test_can_edit_claim_allows_assigned_user_case_insensitively():
    assert can_edit_claim(" assigned ", "APatil", "apatil")


def test_can_edit_claim_uses_mfq_status_case_insensitively():
    assert can_edit_claim(" mfq_generated ", None, "APatil")
    assert can_edit_claim(" rejected ", None, "APatil")
    assert not can_edit_claim(" approved ", "APatil", "APatil")


def test_can_edit_claim_handles_non_string_assignment_values_without_crashing():
    assert not can_edit_claim("On Hold", 12345.0, "12345.0")


class _FakeResult:
    def __init__(self, df):
        self._df = df

    def to_pandas(self):
        return self._df


class _FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.queries = []

    def sql(self, query):
        self.queries.append(query)
        for marker, response in self.responses:
            if marker in query:
                if isinstance(response, Exception):
                    raise response
                return _FakeResult(response)
        raise AssertionError(f"Unexpected query: {query}")


def test_get_current_user_reads_experimental_user_before_sql(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", None, raising=False)
    monkeypatch.setattr(
        rbac_service.st, "experimental_user", {"user_name": "APATIL"}, raising=False
    )
    session = _FakeSession([])

    assert rbac_service.get_current_user(session) == "APATIL"
    assert session.queries == []


def test_get_current_user_falls_back_to_current_user_case_insensitively(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", None, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("CURRENT_USER()", pd.DataFrame([{"current_user": "APATIL"}])),
        ]
    )

    assert rbac_service.get_current_user(session) == "APATIL"


def test_available_roles_for_dropdown_uses_current_available_roles_locally(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", None, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("CURRENT_AVAILABLE_ROLES()", pd.DataFrame([{"ROLE_NAME": "FR_MFQ_APP"}])),
        ]
    )

    assert rbac_service.get_available_roles_for_dropdown(session) == ["FR_MFQ_APP"]
    assert any("CURRENT_AVAILABLE_ROLES()" in query for query in session.queries)
    assert not any("GRANTS_TO_USERS" in query for query in session.queries)


def test_available_roles_for_dropdown_uses_viewer_account_usage_roles(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", {"user_name": "APATIL"}, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            (
                "SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS",
                pd.DataFrame(
                    [
                        {"ROLE_NAME": "FR_MFQ_APPDEV"},
                        {"ROLE_NAME": "FR_MFQ_ANALYST"},
                    ]
                ),
            ),
            ("CURRENT_AVAILABLE_ROLES()", pd.DataFrame([{"ROLE_NAME": "FR_MFQ_ADMIN"}])),
        ]
    )

    assert rbac_service.get_available_roles_for_dropdown(session) == [
        "FR_MFQ_ANALYST",
        "FR_MFQ_APPDEV",
        "PUBLIC",
    ]
    assert any("GRANTEE_NAME = UPPER('APATIL')" in query for query in session.queries)
    assert not any("CURRENT_AVAILABLE_ROLES()" in query for query in session.queries)


def test_available_roles_for_dropdown_falls_back_to_session_roles_when_account_usage_fails(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", {"user_name": "APATIL"}, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS", RuntimeError("not authorized")),
            ("CURRENT_AVAILABLE_ROLES()", pd.DataFrame([{"ROLE_NAME": "FR_MFQ_ADMIN"}])),
        ]
    )

    assert rbac_service.get_available_roles_for_dropdown(session) == ["FR_MFQ_ADMIN"]
    assert any("GRANTS_TO_USERS" in query for query in session.queries)
    assert any("CURRENT_AVAILABLE_ROLES()" in query for query in session.queries)


def test_available_roles_for_dropdown_falls_back_to_current_role(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", {"user_name": "APATIL"}, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS", RuntimeError("not authorized")),
            ("CURRENT_AVAILABLE_ROLES()", RuntimeError("function unavailable")),
            ("CURRENT_ROLE()", pd.DataFrame([{"ROLE_NAME": "FR_MFQ_ADMIN"}])),
        ]
    )

    assert rbac_service.get_available_roles_for_dropdown(session) == ["FR_MFQ_ADMIN"]


def test_available_roles_for_dropdown_returns_unknown_as_last_resort(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", {"user_name": "APATIL"}, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS", RuntimeError("not authorized")),
            ("CURRENT_AVAILABLE_ROLES()", RuntimeError("function unavailable")),
            ("CURRENT_ROLE()", RuntimeError("unavailable")),
        ]
    )

    assert rbac_service.get_available_roles_for_dropdown(session) == ["Unknown"]


def test_get_available_roles_always_includes_current_role():
    session = _FakeSession(
        [
            ("CURRENT_ROLE()", pd.DataFrame([{"ROLE_NAME": "FR_MFQ_APPDEV"}])),
            ("CURRENT_AVAILABLE_ROLES()", pd.DataFrame([{"ROLE_NAME": "FR_MFQ_APP"}])),
        ]
    )

    assert rbac_service.get_available_roles(session) == (
        ["FR_MFQ_APP", "FR_MFQ_APPDEV"],
        "FR_MFQ_APPDEV",
    )
