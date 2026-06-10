from __future__ import annotations

import pandas as pd

from config import snowflake_objects as obj
from core.query_executor import execute_query_df


def get_status_values(session):
    return execute_query_df(session, f"SELECT DISTINCT CLAIM_STATUS AS STATUS FROM {obj.MFQ_CLAIMS_LIST_VIEW} WHERE CLAIM_STATUS IS NOT NULL ORDER BY STATUS", query_name="mfq.get_status")


def get_active_mfq_sections_and_questions(session) -> pd.DataFrame:
    """Return active MFQ reference sections/questions without claim-specific answer data."""
    return execute_query_df(
        session,
        f"""
        SELECT
            s.SECTION_ID,
            NULL AS SECTION_KEY,
            s.SECTION_NAME,
            s.SECTION_DESCRIPTION,
            s.DISPLAY_ORDER AS SECTION_ORDER,
            q.QUESTION_ID,
            NULL AS QUESTION_KEY,
            q.PARENT_QUESTION_ID,
            q.QUESTION_NUMBER,
            q.DISPLAY_ORDER AS QUESTION_ORDER,
            q.QUESTION_TEXT,
            q.ANSWER_TYPE,
            q.ANSWER_OPTIONS,
            q.ANSWER_OPTIONS AS ALLOWED_VALUES,
            NULL AS VISIBILITY_RULE,
            q.REQUIRED_FLAG,
            q.PROMPT_CODE,
            q.RETRIEVAL_KEYWORDS
        FROM {obj.MFQ_SECTIONS_TABLE} s
        JOIN {obj.MFQ_QUESTIONS_TABLE} q
          ON q.SECTION_ID = s.SECTION_ID
        WHERE s.ACTIVE_FLAG = TRUE
          AND q.ACTIVE_FLAG = TRUE
        ORDER BY s.DISPLAY_ORDER, q.DISPLAY_ORDER
        """,
        query_name="mfq.get_active_mfq_sections_and_questions",
    )


def get_mfq_sections(session) -> pd.DataFrame:
    """Backward-compatible alias for active MFQ reference data."""
    return get_active_mfq_sections_and_questions(session)


def get_current_mfq_answers_by_claim_id(session, claim_id: str) -> pd.DataFrame:
    """Return current MFQ answers for one claim in one query."""
    return execute_query_df(
        session,
        f"""
        SELECT
            a.ANSWER_ID,
            a.RUN_ID,
            a.RUN_SCOPE,
            a.RUN_TYPE,
            a.VERSION_NUMBER,
            a.IS_CURRENT,
            a.SUPERSEDED_BY_ANSWER_ID,
            a.CLAIM_ID,
            NULL AS DEFENDANT_ID,
            a.QUESTION_ID,
            a.SECTION_ID AS ANSWER_SECTION_ID,
            a.PACKET_ID,
            a.ANSWER_VALUE,
            a.ANSWER_TEXT,
            a.RATIONALE_TEXT,
            a.CITATIONS_JSON,
            a.CONFIDENCE_SCORE,
            a.ANSWER_STATUS,
            a.ANSWER_STATUS AS STATUS,
            a.EVALUATION_ID,
            a.LLM_INVOCATION_ID,
            a.RAW_RESPONSE_JSON,
            a.RAW_RESPONSE_JSON AS ANSWER_JSON,
            a.CREATED_AT,
            a.UPDATED_AT
        FROM {obj.MFQ_ANSWERS_TABLE} a
        WHERE TRIM(TO_VARCHAR(a.CLAIM_ID)) = TRIM(TO_VARCHAR(?))
          AND a.IS_CURRENT = TRUE
        ORDER BY a.SECTION_ID, a.QUESTION_ID, a.VERSION_NUMBER DESC, a.UPDATED_AT DESC
        """,
        params=[str(claim_id)],
        query_name="mfq.get_current_mfq_answers_by_claim_id",
    )


def get_mfq_answers_by_claim_id(session, claim_id: str) -> pd.DataFrame:
    """Backward-compatible alias for current MFQ answers by claim."""
    return get_current_mfq_answers_by_claim_id(session, claim_id)


def get_mfq_form_payload(session, claim_id: str) -> dict[str, pd.DataFrame]:
    """Repository-level two-query payload for the MFQ form."""
    return {
        "sections_questions": get_active_mfq_sections_and_questions(session),
        "answers": get_current_mfq_answers_by_claim_id(session, claim_id),
    }


def get_claim_summaries(session, claim_id: str) -> pd.DataFrame:
    return execute_query_df(
        session,
        f"""
        SELECT 'RECORD_SUMMARY' AS SUMMARY_TYPE, SUMMARY_TEXT, GENERATED_TS FROM {obj.MFQ_RECORD_SUMMARY_TABLE} WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        UNION ALL
        SELECT 'MEDCRON' AS SUMMARY_TYPE, SUMMARY_TEXT, GENERATED_TS FROM {obj.MFQ_MEDCRON_SUMMARY_TABLE} WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        UNION ALL
        SELECT 'LEGAL_MEMO' AS SUMMARY_TYPE, SUMMARY_TEXT, GENERATED_TS FROM {obj.MFQ_LEGAL_MEMO_TABLE} WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        ORDER BY GENERATED_TS DESC
        """,
        params=[str(claim_id), str(claim_id), str(claim_id)],
        query_name="mfq.get_claim_summaries",
    )


def get_claim_summary_by_type(session, claim_id: str, summary_type: str) -> pd.DataFrame:
    normalized_type = str(summary_type or "").strip().upper()
    summary_sources = {
        "RECORD_SUMMARY": obj.MFQ_RECORD_SUMMARY_TABLE,
        "RECORDS_SUMMARY": obj.MFQ_RECORD_SUMMARY_TABLE,
        "MEDCRON": obj.MFQ_MEDCRON_SUMMARY_TABLE,
        "LEGAL_MEMO": obj.MFQ_LEGAL_MEMO_TABLE,
    }
    source_table = summary_sources.get(normalized_type)
    if source_table is None:
        return pd.DataFrame(columns=["SUMMARY_TYPE", "SUMMARY_TEXT", "GENERATED_TS"])

    canonical_type = "RECORD_SUMMARY" if normalized_type == "RECORDS_SUMMARY" else normalized_type
    return execute_query_df(
        session,
        f"""
        SELECT ? AS SUMMARY_TYPE, SUMMARY_TEXT, GENERATED_TS
        FROM {source_table}
        WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        ORDER BY GENERATED_TS DESC
        LIMIT 1
        """,
        params=[canonical_type, str(claim_id)],
        query_name=f"mfq.get_claim_summary_by_type.{canonical_type}",
    )


def get_section_confidence(session, claim_id: str, section_id: str) -> pd.DataFrame:
    return execute_query_df(
        session,
        f"SELECT CLAIM_ID, SECTION_ID, CONFIDENCE_SCORE FROM {obj.MFQ_SECTION_CONFIDENCE_TABLE} WHERE TRIM(TO_VARCHAR(CLAIM_ID)) = TRIM(TO_VARCHAR(?)) AND SECTION_ID = ?",
        params=[str(claim_id), str(section_id)],
        query_name="mfq.get_section_confidence",
    )


def get_claim_confidence_summary(session, claim_id: str) -> pd.DataFrame:
    return execute_query_df(
        session,
        f"""SELECT s.SECTION_NAME, s.DISPLAY_ORDER AS SECTION_ORDER, sc.CONFIDENCE_SCORE
        FROM {obj.MFQ_SECTION_CONFIDENCE_TABLE} sc
        JOIN {obj.MFQ_SECTIONS_TABLE} s ON s.SECTION_ID = sc.SECTION_ID
        WHERE TRIM(TO_VARCHAR(sc.CLAIM_ID)) = TRIM(TO_VARCHAR(?))
        ORDER BY s.DISPLAY_ORDER, s.SECTION_NAME""",
        params=[str(claim_id)],
        query_name="mfq.get_claim_confidence_summary",
    )


def get_llm_evaluation(session, entity_id: str) -> pd.DataFrame:
    return execute_query_df(session, f"SELECT NEEDS_HUMAN_REVIEW, FAITHFULNESS_SCORE, CREATED_AT FROM {obj.LLM_EVALUATION_TABLE} WHERE ENTITY_ID = ? ORDER BY CREATED_AT DESC LIMIT 1", params=[str(entity_id)], query_name="mfq.get_llm_evaluation")
