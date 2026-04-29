from __future__ import annotations

from collections.abc import Iterable

import streamlit as st

from config import snowflake_objects as obj
from repositories.claims_repository import object_exists

REQUIRED_CORE_OBJECTS = [
    obj.MFQ_RECENT_CLAIMS_VIEW,
    obj.MFQ_CLAIM_DETAIL_VIEW,
    obj.MFQ_FORM_WORKSPACE_VIEW,
    obj.MFQ_ASSIGNMENT_QUEUE_VIEW,
    obj.MFQ_STATUS_HISTORY_TABLE,
    obj.MFQ_SECTION_CONFIDENCE_TABLE,
    obj.LLM_EVALUATION_TABLE,
    obj.MFQ_QUESTIONS_TABLE,
    obj.MFQ_SECTIONS_TABLE,
    obj.MFQ_NOTIFICATIONS_VIEW,
]


def validate_required_objects(session, requirements: Iterable[dict[str, str]] | None = None) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    if requirements is None:
        requirements = [
            {"object_name": name, "expected_location": "CURRENT_SCHEMA", "page": "core"}
            for name in REQUIRED_CORE_OBJECTS
        ]

    for req in requirements:
        object_name = req["object_name"]
        if not object_exists(session, object_name):
            missing.append(req)
    return missing


def render_missing_objects(missing: list[dict[str, str]]) -> None:
    if not missing:
        return
    st.error("Some required Snowflake objects are missing. Please contact support or verify deployment.")
    for item in missing:
        st.markdown(f"- Missing object `{item['object_name']}` (dependency: `{item['page']}`)")
