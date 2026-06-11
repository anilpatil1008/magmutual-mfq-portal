from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import pandas as pd

from components import layout


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_header_profile_card_only_shows_required_profile_fields(monkeypatch):
    captured = {"markdown": [], "popovers": []}
    session_state = {
        "available_roles": ["FR_MFQ_APP"],
        "selected_app_role": "FR_MFQ_APP",
        "username": "jdoe",
        "user_email": "jdoe@example.com",
    }

    def _selectbox(label, options, index=0, key=None, label_visibility=None):
        return options[index]

    def _markdown(body, unsafe_allow_html=False):
        captured["markdown"].append(body)

    @contextmanager
    def _popover(label, **kwargs):
        captured["popovers"].append(label)
        yield _Context()

    monkeypatch.setattr(
        layout,
        "st",
        SimpleNamespace(session_state=session_state, selectbox=_selectbox, markdown=_markdown),
    )
    monkeypatch.setattr(layout, "safe_container", lambda **kwargs: _Context())
    monkeypatch.setattr(layout, "safe_child_container", lambda container, **kwargs: _Context())
    monkeypatch.setattr(layout, "safe_child_columns", lambda container, specs, gap=None: [_Context(), _Context(), _Context()])
    monkeypatch.setattr(layout, "safe_popover", _popover)
    monkeypatch.setattr(layout, "render_notification_center", lambda notifications_df: None)

    ctx = SimpleNamespace(username="jdoe", display_name="Jane Doe", email="jdoe@example.com", sf_role="FR_MFQ_APP")

    layout.render_header(session=object(), ctx=ctx, notifications_df=pd.DataFrame({"IS_READ": [True]}))

    profile_html = next(markup for markup in captured["markdown"] if "mm-profile-card" in markup)

    assert "mm-avatar mm-avatar-lg" in profile_html
    assert "Username" in profile_html
    assert "Snowflake Role" in profile_html
    assert "Email" in profile_html
    assert "Name" not in profile_html
    assert "Runtime Owner Role" not in profile_html
    assert any("Jane Doe" in label for label in captured["popovers"])
