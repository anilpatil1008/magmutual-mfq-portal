from __future__ import annotations

import inspect
import os
import sys
from contextlib import contextmanager
from typing import Any, Iterator

import streamlit as st


def supports_param(func: Any, param_name: str) -> bool:
    try:
        return param_name in inspect.signature(func).parameters
    except Exception:
        return False


def _supported_kwargs(func: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    try:
        supported_params = inspect.signature(func).parameters
        return {
            key: value
            for key, value in kwargs.items()
            if key in supported_params
        }
    except Exception:
        return {}


def safe_set_page_config(**kwargs: Any) -> None:
    """Set page config without failing older Snowflake Streamlit runtimes."""
    try:
        set_page_config = getattr(st, "set_page_config")
        set_page_config(**_supported_kwargs(set_page_config, kwargs))
    except Exception:
        try:
            minimal_kwargs = {key: kwargs[key] for key in ("page_title", "layout") if key in kwargs}
            getattr(st, "set_page_config")(**minimal_kwargs)
        except Exception:
            pass


def safe_container(**kwargs: Any):
    try:
        container = getattr(st, "container")
        return container(**_supported_kwargs(container, kwargs))
    except Exception:
        return getattr(st, "container")()


def safe_child_container(parent: Any, **kwargs: Any):
    """Create a child container without passing unsupported runtime parameters."""
    container_func = getattr(parent, "container", None)
    if container_func is None:
        return safe_container(**kwargs)

    try:
        return container_func(**_supported_kwargs(container_func, kwargs))
    except Exception:
        return container_func()


def safe_columns(spec: Any, **kwargs: Any):
    try:
        columns = getattr(st, "columns")
        return columns(spec, **_supported_kwargs(columns, kwargs))
    except Exception:
        return getattr(st, "columns")(spec)


def safe_child_columns(parent: Any, spec: Any, **kwargs: Any):
    """Create columns on a parent container without unsupported parameters."""
    columns_func = getattr(parent, "columns", None)
    if columns_func is None:
        return safe_columns(spec, **kwargs)

    try:
        return columns_func(spec, **_supported_kwargs(columns_func, kwargs))
    except Exception:
        return columns_func(spec)


def safe_dataframe(data: Any = None, **kwargs: Any):
    try:
        dataframe = getattr(st, "dataframe")
        return dataframe(data, **_supported_kwargs(dataframe, kwargs))
    except Exception:
        return getattr(st, "dataframe")(data)


def safe_button(label: str, **kwargs: Any) -> bool:
    """
    Snowflake-safe button wrapper.

    Removes unsupported keyword arguments such as icon while preserving
    supported behavior in newer Streamlit runtimes. If a runtime exposes a
    keyword but rejects a newer value (for example, a newer button ``type``),
    retry with non-behavioral styling arguments removed.
    """
    button = getattr(st, "button")
    safe_kwargs = _supported_kwargs(button, kwargs)
    try:
        return bool(button(label, **safe_kwargs))
    except Exception:
        pass

    fallback_kwargs = dict(safe_kwargs)
    fallback_kwargs.pop("icon", None)
    fallback_kwargs.pop("type", None)
    try:
        return bool(button(label, **_supported_kwargs(button, fallback_kwargs)))
    except Exception:
        minimal_kwargs = {
            key: value
            for key, value in fallback_kwargs.items()
            if key in ("key", "help", "on_click", "args", "kwargs", "disabled", "use_container_width")
        }
        try:
            return bool(button(label, **_supported_kwargs(button, minimal_kwargs)))
        except Exception:
            return bool(button(label))


def safe_download_button(label: str, data: Any, **kwargs: Any) -> bool:
    """
    Snowflake-safe download button wrapper.

    Removes unsupported keyword arguments such as icon while keeping downloads
    functional in older Snowflake Streamlit runtimes.
    """
    try:
        download_button = getattr(st, "download_button")
        return bool(download_button(label, data=data, **_supported_kwargs(download_button, kwargs)))
    except Exception:
        filename = kwargs.get("file_name")
        mime = kwargs.get("mime")
        key = kwargs.get("key")
        return bool(getattr(st, "download_button")(label, data=data, file_name=filename, mime=mime, key=key))


def safe_rerun(streamlit_module: Any = None) -> None:
    runtime_st = streamlit_module or st
    rerun_func = getattr(runtime_st, "rerun", None) or getattr(runtime_st, "experimental_rerun", None)
    if rerun_func is not None:
        rerun_func()


def has_dialog() -> bool:
    return hasattr(st, "dialog") or hasattr(st, "experimental_dialog")


def safe_dialog(title: str, **kwargs: Any):
    dialog_func = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
    if dialog_func is None:
        return None

    try:
        return dialog_func(title, **_supported_kwargs(dialog_func, kwargs))
    except Exception:
        return dialog_func(title)


@contextmanager
def safe_popover(label: str, **kwargs: Any) -> Iterator[Any]:
    """
    Use popover when available. Fall back to expander in older runtimes.
    """
    popover_func = getattr(st, "popover", None)
    if popover_func is not None:
        try:
            popover = popover_func(label, **_supported_kwargs(popover_func, kwargs))
            popover_value = popover.__enter__()
        except Exception:
            pass
        else:
            try:
                yield popover_value
            except BaseException:
                if not popover.__exit__(*sys.exc_info()):
                    raise
            else:
                popover.__exit__(None, None, None)
            return

    expander_kwargs = {"expanded": kwargs.get("expanded", False)}
    expander_func = getattr(st, "expander")
    with expander_func(label, **_supported_kwargs(expander_func, expander_kwargs)):
        yield


def safe_toast(message: str, **kwargs: Any) -> None:
    toast_func = getattr(st, "toast", None)
    if toast_func is not None:
        try:
            toast_func(message, **_supported_kwargs(toast_func, kwargs))
            return
        except Exception:
            pass
    st.info(message)


def safe_segmented_control(label: str, options: Any, **kwargs: Any):
    """
    Use segmented_control when available. Fall back to radio in older runtimes.
    """
    segmented_control = getattr(st, "segmented_control", None)
    if segmented_control is not None:
        try:
            return segmented_control(label, options, **_supported_kwargs(segmented_control, kwargs))
        except Exception:
            pass

    radio_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key in ("index", "key", "help", "horizontal", "label_visibility")
    }
    return st.radio(label, options, **radio_kwargs)


def is_debug_enabled() -> bool:
    return os.getenv("APP_DEBUG", "false").lower() in ("1", "true", "yes", "y")
