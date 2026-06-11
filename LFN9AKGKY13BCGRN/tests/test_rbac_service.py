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
    def __init__(self, response):
        self._response = response

    def to_pandas(self):
        return self._response

    def collect(self):
        if isinstance(self._response, pd.DataFrame):
            return self._response.to_dict("records")
        return self._response or []


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


def test_available_roles_for_dropdown_uses_show_grants_for_streamlit_viewer(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", {"user_name": "APATIL"}, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("SHOW GRANTS TO USER", []),
            (
                "RESULT_SCAN(LAST_QUERY_ID())",
                [
                    {"ROLE_NAME": "FR_MFQ_APPDEV"},
                    {"ROLE_NAME": "OTHER_ROLE"},
                    {"ROLE_NAME": "FR_MFQ_ANALYST"},
                ],
            ),
            ("CURRENT_ROLE()", pd.DataFrame([{"ROLE_NAME": "FR_MFQ_ADMIN"}])),
        ]
    )

    assert rbac_service.get_available_roles_for_dropdown(session) == [
        "FR_MFQ_ANALYST",
        "FR_MFQ_APPDEV",
    ]
    assert any('SHOW GRANTS TO USER "APATIL"' in query for query in session.queries)
    assert any("RESULT_SCAN(LAST_QUERY_ID())" in query for query in session.queries)
    assert not any("CURRENT_AVAILABLE_ROLES()" in query for query in session.queries)
    assert not any("GRANTS_TO_USERS" in query for query in session.queries)


def test_available_roles_for_dropdown_falls_back_to_current_user_when_st_user_missing(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", None, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("CURRENT_USER()", pd.DataFrame([{"USER_NAME": "APATIL"}])),
            ("SHOW GRANTS TO USER", []),
            ("RESULT_SCAN(LAST_QUERY_ID())", [{"ROLE_NAME": "FR_MFQ_APP"}]),
        ]
    )

    assert rbac_service.get_available_roles_for_dropdown(session) == ["FR_MFQ_APP"]
    assert any('SHOW GRANTS TO USER "APATIL"' in query for query in session.queries)


def test_available_roles_for_dropdown_escapes_viewer_identifier(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", {"user_name": 'A"PATIL'}, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("SHOW GRANTS TO USER", []),
            ("RESULT_SCAN(LAST_QUERY_ID())", [{"ROLE_NAME": "FR_MFQ_APP"}]),
        ]
    )

    assert rbac_service.get_available_roles_for_dropdown(session) == ["FR_MFQ_APP"]
    assert any('SHOW GRANTS TO USER "A""PATIL"' in query for query in session.queries)


def test_available_roles_for_dropdown_falls_back_to_current_role(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", {"user_name": "APATIL"}, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("SHOW GRANTS TO USER", RuntimeError("not authorized")),
            ("CURRENT_ROLE()", pd.DataFrame([{"ROLE_NAME": "FR_MFQ_ADMIN"}])),
        ]
    )

    assert rbac_service.get_available_roles_for_dropdown(session) == ["FR_MFQ_ADMIN"]


def test_available_roles_for_dropdown_returns_unknown_as_last_resort(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", {"user_name": "APATIL"}, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    session = _FakeSession(
        [
            ("SHOW GRANTS TO USER", RuntimeError("not authorized")),
            ("CURRENT_ROLE()", RuntimeError("unavailable")),
        ]
    )

    assert rbac_service.get_available_roles_for_dropdown(session) == ["Unknown"]


def test_get_available_roles_returns_dropdown_options_and_owner_role_context():
    session = _FakeSession(
        [
            ("CURRENT_ROLE()", pd.DataFrame([{"ROLE_NAME": "FR_MFQ_APPDEV"}])),
            ("CURRENT_USER()", pd.DataFrame([{"USER_NAME": "APATIL"}])),
            ("SHOW GRANTS TO USER", []),
            ("RESULT_SCAN(LAST_QUERY_ID())", [{"ROLE_NAME": "FR_MFQ_APP"}]),
        ]
    )

    assert rbac_service.get_available_roles(session) == (
        ["FR_MFQ_APP"],
        "FR_MFQ_APPDEV",
    )


def test_selected_app_role_defaults_to_appdev_when_available(monkeypatch):
    monkeypatch.setattr(rbac_service.st, "user", {"user_name": "APATIL"}, raising=False)
    monkeypatch.setattr(rbac_service.st, "experimental_user", None, raising=False)
    rbac_service.st.session_state.pop("selected_app_role", None)
    rbac_service.st.session_state.pop("selected_sf_role", None)
    session = _FakeSession(
        [
            ("SHOW GRANTS TO USER", []),
            (
                "RESULT_SCAN(LAST_QUERY_ID())",
                [
                    {"ROLE_NAME": "FR_MFQ_ADMIN"},
                    {"ROLE_NAME": "FR_MFQ_APPDEV"},
                ],
            ),
            ("CURRENT_ROLE()", pd.DataFrame([{"ROLE_NAME": "FR_MFQ_ADMIN"}])),
        ]
    )

    assert rbac_service.get_selected_sf_role(session) == "FR_MFQ_APPDEV"
    assert rbac_service.st.session_state["selected_app_role"] == "FR_MFQ_APPDEV"
    assert rbac_service.st.session_state["selected_sf_role"] == "FR_MFQ_APPDEV"
