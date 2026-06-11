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


def test_available_roles_uses_show_grants_fallback_when_current_available_roles_fails():
    session = _FakeSession(
        [
            ("CURRENT_AVAILABLE_ROLES()", RuntimeError("function unavailable")),
            ("CURRENT_USER()", pd.DataFrame([{"USER_NAME": "APATIL"}])),
            (
                "SHOW GRANTS TO USER",
                pd.DataFrame(
                    [
                        {"granted_to": "ROLE", "role": "FR_MFQ_APP"},
                        {"granted_to": "ROLE", "role": "FR_MFQ_APPDEV"},
                        {"granted_to": "WAREHOUSE", "role": "IGNORED_WAREHOUSE"},
                    ]
                ),
            ),
        ]
    )

    assert rbac_service.get_available_roles_for_current_user(session) == [
        "FR_MFQ_APP",
        "FR_MFQ_APPDEV",
    ]
    assert any('SHOW GRANTS TO USER "APATIL"' in query for query in session.queries)


def test_available_roles_merges_streamlit_user_grants_with_current_available_roles(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", {"user_name": "APATIL"}, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("CURRENT_AVAILABLE_ROLES()", pd.DataFrame([{"ROLE_NAME": "FR_MFQ_APP"}])),
            (
                "SHOW GRANTS TO USER",
                pd.DataFrame(
                    [
                        {"granted_to": "USER", "role": "FR_MFQ_APPDEV"},
                        {"granted_to": "USER", "role": "FR_MFQ_ADMIN"},
                    ]
                ),
            ),
        ]
    )

    assert rbac_service.get_available_roles_for_current_user(session) == [
        "FR_MFQ_ADMIN",
        "FR_MFQ_APP",
        "FR_MFQ_APPDEV",
    ]
    assert any('SHOW GRANTS TO USER "APATIL"' in query for query in session.queries)
    assert not any("CURRENT_USER()" in query for query in session.queries)


def test_available_roles_retries_uppercase_snowflake_username(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", {"user_name": "apatil"}, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("CURRENT_AVAILABLE_ROLES()", RuntimeError("function unavailable")),
            ('SHOW GRANTS TO USER "apatil"', RuntimeError("user does not exist")),
            (
                'SHOW GRANTS TO USER "APATIL"',
                pd.DataFrame([{"granted_to": "USER", "role": "FR_MFQ_APPDEV"}]),
            ),
        ]
    )

    assert rbac_service.get_available_roles_for_current_user(session) == ["FR_MFQ_APPDEV"]
    assert any('SHOW GRANTS TO USER "apatil"' in query for query in session.queries)
    assert any('SHOW GRANTS TO USER "APATIL"' in query for query in session.queries)


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


def test_role_selector_state_defaults_to_current_role_from_available_roles():
    assert rbac_service.get_role_selector_state(
        ["FR_MFQ_ADMIN", "FR_MFQ_APP"],
        "FR_MFQ_APP",
    ) == (["FR_MFQ_ADMIN", "FR_MFQ_APP"], "FR_MFQ_APP")


def test_role_selector_state_preserves_valid_user_selection():
    assert rbac_service.get_role_selector_state(
        ["FR_MFQ_ADMIN", "FR_MFQ_APP"],
        "FR_MFQ_APP",
        "FR_MFQ_ADMIN",
    ) == (["FR_MFQ_ADMIN", "FR_MFQ_APP"], "FR_MFQ_ADMIN")


def test_role_selector_state_includes_current_role_when_available_roles_omit_it():
    assert rbac_service.get_role_selector_state(
        ["FR_MFQ_APP"],
        "FR_MFQ_APPDEV",
    ) == (["FR_MFQ_APP", "FR_MFQ_APPDEV"], "FR_MFQ_APPDEV")
