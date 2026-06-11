from __future__ import annotations

from core import snowflake_session


class _FakeBuilder:
    def __init__(self) -> None:
        self.parameters = None

    def configs(self, parameters):
        self.parameters = parameters
        return self

    def create(self):
        return {"created_with": self.parameters}


class _FakeSession:
    builder = _FakeBuilder()


def test_get_snowflake_session_returns_active_session_before_local_config(monkeypatch):
    active_session = object()

    snowflake_session.get_snowflake_session.clear()
    monkeypatch.setattr(snowflake_session, "_get_active_session", lambda: active_session)
    monkeypatch.setattr(
        snowflake_session,
        "_build_connection_parameters",
        lambda: (_ for _ in ()).throw(AssertionError("local config should not be read")),
    )

    assert snowflake_session.get_snowflake_session() is active_session


def test_get_snowflake_session_falls_back_to_local_config(monkeypatch):
    parameters = {"account": "acct", "user": "user", "password": "pw"}

    snowflake_session.get_snowflake_session.clear()
    monkeypatch.setattr(snowflake_session, "_get_active_session", lambda: None)
    monkeypatch.setattr(snowflake_session, "_build_connection_parameters", lambda: parameters)
    monkeypatch.setattr(snowflake_session, "Session", _FakeSession)

    assert snowflake_session.get_snowflake_session() == {"created_with": parameters}
