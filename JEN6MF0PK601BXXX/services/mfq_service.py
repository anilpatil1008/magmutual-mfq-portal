from __future__ import annotations

from core.constants import EDIT_ALL_ROLES, ROLE_MEDICAL_FACULTY
from core.session import get_session
from repositories.base_repository import esc
from repositories.mfq_repository import get_sections
from config.settings import CONFIG


def guidance_from_confidence(score: float) -> str:
    if score < 80:
        return "Faculty Review Might Be Needed"
    if score < 90:
        return "Analyst Discretion Required"
    return "Confidence Looks Strong"


def save_answer(
    claim_id: str,
    defendant_id: str,
    question_id: str,
    question_key: str,
    answer_raw: str,
    answer_text: str,
    user_id: str,
) -> None:
    session = get_session()
    if session is None:
        raise RuntimeError("Save works only inside Streamlit in Snowflake.")

    session.sql(f"""
        UPDATE {CONFIG.database}.{CONFIG.schema}.MFQ_ANSWER
        SET IS_CURRENT = FALSE
        WHERE CLAIM_ID = '{esc(claim_id)}'
          AND DEFENDANT_ID = '{esc(defendant_id)}'
          AND QUESTION_ID = '{esc(question_id)}'
          AND IS_CURRENT = TRUE
    """).collect()

    session.sql(f"""
        INSERT INTO {CONFIG.database}.{CONFIG.schema}.MFQ_ANSWER
        (
            ANSWER_ID,
            CLAIM_ID,
            DEFENDANT_ID,
            QUESTION_ID,
            QUESTION_KEY,
            ANSWER_VERSION,
            IS_CURRENT,
            ANSWER_RAW,
            ANSWER_TEXT,
            CONFIDENCE_SCORE,
            STATUS,
            UPDATED_BY,
            UPDATED_AT
        )
        SELECT
            UUID_STRING(),
            '{esc(claim_id)}',
            '{esc(defendant_id)}',
            '{esc(question_id)}',
            '{esc(question_key)}',
            COALESCE(MAX(ANSWER_VERSION), 0) + 1,
            TRUE,
            '{esc(answer_raw)}',
            '{esc(answer_text)}',
            100,
            'HUMAN_UPDATED',
            '{esc(user_id)}',
            CURRENT_TIMESTAMP()
        FROM {CONFIG.database}.{CONFIG.schema}.MFQ_ANSWER
        WHERE CLAIM_ID = '{esc(claim_id)}'
          AND DEFENDANT_ID = '{esc(defendant_id)}'
          AND QUESTION_ID = '{esc(question_id)}'
    """).collect()


def get_editable_sections(claim_id: str, user_id: str, role_key: str) -> set[str]:
    if role_key in EDIT_ALL_ROLES:
        sections = get_sections()
        return set(sections["SECTION_KEY"].tolist())

    if role_key != ROLE_MEDICAL_FACULTY:
        return set()

    session = get_session()
    df = session.sql(f"""
        SELECT sa.SECTION_KEY
        FROM {CONFIG.database}.{CONFIG.schema}.SECTION_ASSIGNMENT sa
        JOIN {CONFIG.database}.{CONFIG.schema}.CLAIM_ASSIGNMENT ca
          ON sa.ASSIGNMENT_ID = ca.ASSIGNMENT_ID
        WHERE sa.CLAIM_ID = '{esc(claim_id)}'
          AND ca.ASSIGNED_TO_USER_ID = '{esc(user_id)}'
          AND ca.ASSIGNMENT_STATUS = 'ASSIGNED'
          AND sa.IS_EDITABLE = TRUE
    """).to_pandas()

    return set(df["SECTION_KEY"].tolist())