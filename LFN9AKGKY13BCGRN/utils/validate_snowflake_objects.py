from __future__ import annotations

from collections.abc import Iterable

import streamlit as st

from config import snowflake_objects as obj
from repositories.claims_repository import object_exists

REQUIRED_CORE_OBJECTS = [
    obj.MFQ_CLAIMS_LIST_VIEW,
    obj.MFQ_RECENT_CLAIMS_VIEW,
    obj.MFQ_DASHBOARD_SUMMARY_VIEW,
    obj.MFQ_CLAIM_DETAIL_VW,
    obj.MFQ_FORM_WORKSPACE_VIEW,
    obj.MFQ_ANSWERS_TABLE,
    obj.MFQ_ASSIGNMENT_QUEUE_VIEW,
    obj.MFQ_STATUS_HISTORY_TABLE,
    obj.MFQ_SECTION_CONFIDENCE_TABLE,
    obj.LLM_EVALUATION_TABLE,
    obj.MFQ_QUESTIONS_TABLE,
    obj.MFQ_SECTIONS_TABLE,
    obj.MFQ_NOTIFICATIONS_VIEW,
]


@st.cache_data(ttl=300, show_spinner=False)
def validate_required_objects(_session, requirements: tuple[tuple[str, str, str], ...] | None = None) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    normalized_requirements: list[dict[str, str]] = []
    if requirements is None:
        normalized_requirements = [
            {"object_name": name, "expected_location": "CURRENT_SCHEMA", "page": "core"}
            for name in REQUIRED_CORE_OBJECTS
        ]
    else:
        normalized_requirements = [
            {"object_name": obj_name, "expected_location": expected_location, "page": page}
            for obj_name, expected_location, page in requirements
        ]

    for req in normalized_requirements:
        object_name = req["object_name"]
        if not object_exists(_session, object_name):
            missing.append(req)
    return missing


def render_missing_objects(missing: list[dict[str, str]]) -> None:
    if not missing:
        return
    st.error("Some required Snowflake objects are missing. Please contact support or verify deployment.")
    for item in missing:
        st.markdown(f"- Missing object `{item['object_name']}` (dependency: `{item['page']}`)")
