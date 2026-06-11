from __future__ import annotations

from contextlib import contextmanager
import inspect
import os
from typing import Any, Callable, Iterator

import streamlit as st


def supports_param(func, param_name: str) -> bool:
    try:
        return param_name in inspect.signature(func).parameters
    except Exception:
        return False


def _supported_kwargs(func: Callable[..., Any], kwargs: dict[str, Any]) -> dict[str, Any]:
    try:
        supported_params = inspect.signature(func).parameters
        return {key: value for key, value in kwargs.items() if key in supported_params}
    except Exception:
        return {}


def safe_container(**kwargs):
    try:
        supported_params = inspect.signature(st.container).parameters
        safe_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key in supported_params
        }
        return st.container(**safe_kwargs)
    except Exception:
        return st.container()


def safe_child_container(parent, **kwargs):
    """Create a child container without passing unsupported runtime parameters."""
    container_func = getattr(parent, "container", None)
    if container_func is None:
        return safe_container(**kwargs)

    try:
        return container_func(**_supported_kwargs(container_func, kwargs))
    except Exception:
        return container_func()


def safe_columns(spec, **kwargs):
    try:
        return st.columns(spec, **_supported_kwargs(st.columns, kwargs))
    except Exception:
        return st.columns(spec)


def safe_dataframe(data=None, **kwargs):
    try:
        return st.dataframe(data, **_supported_kwargs(st.dataframe, kwargs))
    except Exception:
        return st.dataframe(data)


def safe_rerun(streamlit_module=None):
    runtime_st = streamlit_module or st
    if hasattr(runtime_st, "rerun"):
        runtime_st.rerun()
    elif hasattr(runtime_st, "experimental_rerun"):
        runtime_st.experimental_rerun()


def has_dialog():
    return hasattr(st, "dialog") or hasattr(st, "experimental_dialog")


def safe_dialog(title, **kwargs):
    if hasattr(st, "dialog"):
        try:
            return st.dialog(title, **_supported_kwargs(st.dialog, kwargs))
        except Exception:
            return st.dialog(title)

    if hasattr(st, "experimental_dialog"):
        try:
            supported_params = inspect.signature(st.experimental_dialog).parameters
            safe_kwargs = {
                key: value
                for key, value in kwargs.items()
                if key in supported_params
            }
            return st.experimental_dialog(title, **safe_kwargs)
        except Exception:
            return st.experimental_dialog(title)

    return None


@contextmanager
def safe_popover(label: str, **kwargs) -> Iterator[None]:
    """Use st.popover when available, otherwise fall back to st.expander."""
    if hasattr(st, "popover"):
        try:
            with st.popover(label, **_supported_kwargs(st.popover, kwargs)):
                yield
            return
        except Exception:
            pass

    expander_kwargs = {"expanded": kwargs.get("expanded", False)}
    with st.expander(label, **_supported_kwargs(st.expander, expander_kwargs)):
        yield


def safe_toast(message: str, **kwargs) -> None:
    if hasattr(st, "toast"):
        try:
            st.toast(message, **_supported_kwargs(st.toast, kwargs))
            return
        except Exception:
            pass
    st.info(message)


def is_debug_enabled() -> bool:
    return os.getenv("APP_DEBUG", "false").lower() in ("1", "true", "yes", "y")
