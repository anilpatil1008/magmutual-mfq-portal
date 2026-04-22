from __future__ import annotations

from config.settings import CONFIG
from repositories.base_repository import run_query, exec_sql, esc


def get_sections():
    return run_query(f"""
        SELECT SECTION_ID, SECTION_KEY, SECTION_NAME, DISPLAY_ORDER
        FROM {CONFIG.database}.{CONFIG.schema}.QST_SECTION
        WHERE FORM_KEY = '{CONFIG.form_key}' AND IS_ACTIVE = TRUE
        ORDER BY DISPLAY_ORDER
    """)


def get_questions_by_section(section_id: str):
    return run_query(f"""
        SELECT QUESTION_ID, QUESTION_KEY, QUESTION_TEXT, ANSWER_TYPE, ALLOWED_VALUES, DISPLAY_ORDER
        FROM {CONFIG.database}.{CONFIG.schema}.QST_QUESTION
        WHERE SECTION_ID = '{esc(section_id)}' AND IS_ACTIVE = TRUE
        ORDER BY DISPLAY_ORDER
    """)


def get_current_answers(claim_id: str, defendant_id: str):
    return run_query(f"""
        SELECT QUESTION_ID, QUESTION_KEY, ANSWER_RAW, ANSWER_TEXT, CONFIDENCE_SCORE, STATUS, UPDATED_BY, UPDATED_AT
        FROM {CONFIG.database}.{CONFIG.schema}.MFQ_ANSWER
        WHERE CLAIM_ID = '{esc(claim_id)}'
          AND DEFENDANT_ID = '{esc(defendant_id)}'
          AND IS_CURRENT = TRUE
    """)


def get_section_confidence(claim_id: str, defendant_id: str):
    return run_query(f"""
        SELECT SECTION_KEY, CONFIDENCE_SCORE, REVIEW_GUIDANCE
        FROM {CONFIG.database}.{CONFIG.schema}.SECTION_CONFIDENCE
        WHERE CLAIM_ID = '{esc(claim_id)}'
          AND DEFENDANT_ID = '{esc(defendant_id)}'
        ORDER BY SECTION_KEY
    """)


def get_claim_summaries(claim_id: str, defendant_id: str):
    return run_query(f"""
        SELECT SUMMARY_TYPE, SUMMARY_TEXT
        FROM {CONFIG.database}.{CONFIG.schema}.CLAIM_SUMMARY
        WHERE CLAIM_ID = '{esc(claim_id)}'
          AND DEFENDANT_ID = '{esc(defendant_id)}'
          AND IS_CURRENT = TRUE
        ORDER BY SUMMARY_TYPE
    """)


def save_answer(claim_id: str, defendant_id: str, question_id: str, question_key: str,
                answer_raw: str, answer_text: str, user_id: str) -> None:
    exec_sql(f"""
        UPDATE {CONFIG.database}.{CONFIG.schema}.MFQ_ANSWER
        SET IS_CURRENT = FALSE
        WHERE CLAIM_ID = '{esc(claim_id)}'
          AND DEFENDANT_ID = '{esc(defendant_id)}'
          AND QUESTION_ID = '{esc(question_id)}'
          AND IS_CURRENT = TRUE
    """)

    exec_sql(f"""
        INSERT INTO {CONFIG.database}.{CONFIG.schema}.MFQ_ANSWER
        (ANSWER_ID, CLAIM_ID, DEFENDANT_ID, QUESTION_ID, QUESTION_KEY, ANSWER_VERSION, IS_CURRENT,
         ANSWER_RAW, ANSWER_TEXT, CONFIDENCE_SCORE, STATUS, UPDATED_BY, UPDATED_AT)
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
    """)
