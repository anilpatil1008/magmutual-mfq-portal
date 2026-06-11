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


def test_externalbrowser_local_config_does_not_require_password(monkeypatch):
    monkeypatch.setattr(
        snowflake_session,
        "_read_streamlit_secrets",
        lambda: {
            "account": "acct",
            "user": "user",
            "authenticator": "externalbrowser",
            "role": "role",
            "warehouse": "wh",
            "database": "db",
            "schema": "schema",
        },
    )
    monkeypatch.setattr(snowflake_session, "_read_environment_variables", lambda: {})

    params = snowflake_session._build_connection_parameters()

    assert params["authenticator"] == "externalbrowser"
    assert "password" not in params


def test_password_local_config_requires_password(monkeypatch):
    monkeypatch.setattr(
        snowflake_session,
        "_read_streamlit_secrets",
        lambda: {
            "account": "acct",
            "user": "user",
            "role": "role",
            "warehouse": "wh",
            "database": "db",
            "schema": "schema",
        },
    )
    monkeypatch.setattr(snowflake_session, "_read_environment_variables", lambda: {})

    try:
        snowflake_session._build_connection_parameters()
    except RuntimeError as exc:
        assert "password" in str(exc)
    else:
        raise AssertionError("password login should require password")
