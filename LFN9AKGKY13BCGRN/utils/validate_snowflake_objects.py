from __future__ import annotations

import streamlit as st

from config import snowflake_objects as obj
from repositories.claims_repository import object_exists, object_location

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


@st.cache_data(ttl=300, show_spinner=False)
def validate_required_objects(_session, requirements: tuple[tuple[str, str, str], ...] | None = None) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
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
        location = object_location(_session, object_name)
        if not object_exists(_session, object_name):
            missing.append({**req, "resolved_location": location})
    return missing


def render_missing_objects(missing: list[dict[str, str]]) -> None:
    if not missing:
        return
    st.error("Some required Snowflake objects are missing. Please contact support or verify deployment.")
    for item in missing:
        st.markdown(
            f"- `{item['object_name']}` not found in `{item.get('resolved_location', item.get('expected_location', 'CURRENT_SCHEMA'))}` "
            f"(dependency: `{item['page']}`)"
        )
