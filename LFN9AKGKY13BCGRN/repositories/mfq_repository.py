from __future__ import annotations
import pandas as pd
from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql

def get_status_values(session):
    return execute_query_df(session, f"SELECT DISTINCT CLAIM_STATUS AS STATUS FROM {obj.MFQ_CLAIMS_LIST_VIEW} WHERE CLAIM_STATUS IS NOT NULL ORDER BY STATUS", query_name="mfq.get_status")

def get_mfq_form_workspace(session, claim_id: str, answer_value_expr: str, generated_answer_expr: str, reviewed_answer_expr: str, qc_level_expr: str, qc_reason_expr: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"""
    SELECT s.SECTION_ID,s.SECTION_KEY,s.SECTION_NAME,s.DISPLAY_ORDER AS SECTION_ORDER,
    q.QUESTION_ID,q.QUESTION_KEY,q.PARENT_QUESTION_ID,q.DISPLAY_ORDER AS QUESTION_ORDER,
    q.QUESTION_TEXT,q.ANSWER_TYPE,q.ALLOWED_VALUES,q.VISIBILITY_RULE,
    a.ANSWER_ID,a.CLAIM_ID,a.DEFENDANT_ID,a.ANSWER_TEXT,a.ANSWER_JSON,
    {answer_value_expr} AS ANSWER_VALUE,{generated_answer_expr} AS GENERATED_ANSWER,{reviewed_answer_expr} AS REVIEWED_ANSWER,
    a.CONFIDENCE_SCORE,a.STATUS AS ANSWER_STATUS,a.IS_CURRENT,{qc_level_expr} AS CONFIDENCE_LEVEL,{qc_reason_expr} AS CONFIDENCE_REASON
    FROM {obj.MFQ_SECTIONS_TABLE} s
    JOIN {obj.MFQ_QUESTIONS_TABLE} q ON q.SECTION_ID=s.SECTION_ID AND q.FORM_KEY=s.FORM_KEY
    LEFT JOIN {obj.MFQ_ANSWERS_TABLE} a ON a.QUESTION_ID=q.QUESTION_ID AND a.CLAIM_ID='{claim_q}' AND a.IS_CURRENT=TRUE
    LEFT JOIN {obj.MFQ_QUESTION_CONFIDENCE_TABLE} qc ON qc.QUESTION_ID=q.QUESTION_ID AND qc.CLAIM_ID='{claim_q}'
    WHERE s.FORM_KEY='MFQ_V1' AND s.IS_ACTIVE=TRUE AND q.IS_ACTIVE=TRUE AND q.IS_CURRENT=TRUE
    ORDER BY s.DISPLAY_ORDER, q.DISPLAY_ORDER
    """, query_name="mfq.get_form_workspace")


def get_claim_summaries(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(
        session,
        f"""
        SELECT 'RECORD_SUMMARY' AS SUMMARY_TYPE, SUMMARY_TEXT, GENERATED_TS FROM {obj.MFQ_RECORD_SUMMARY_TABLE} WHERE CLAIM_ID = '{claim_q}'
        UNION ALL
        SELECT 'MEDCRON' AS SUMMARY_TYPE, SUMMARY_TEXT, GENERATED_TS FROM {obj.MFQ_MEDCRON_SUMMARY_TABLE} WHERE CLAIM_ID = '{claim_q}'
        UNION ALL
        SELECT 'LEGAL_MEMO' AS SUMMARY_TYPE, SUMMARY_TEXT, GENERATED_TS FROM {obj.MFQ_LEGAL_MEMO_TABLE} WHERE CLAIM_ID = '{claim_q}'
        ORDER BY GENERATED_TS DESC
        """,
        query_name="mfq.get_claim_summaries",
    )


def get_section_confidence(session, claim_id: str, section_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    section_q = quote_sql(section_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,SECTION_ID,CONFIDENCE_SCORE FROM {obj.MFQ_SECTION_CONFIDENCE_TABLE} WHERE CLAIM_ID='{claim_q}' AND SECTION_ID='{section_q}'", query_name="mfq.get_section_confidence")


def get_claim_confidence_summary(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(
        session,
        f"""SELECT s.SECTION_NAME,s.DISPLAY_ORDER AS SECTION_ORDER,sc.CONFIDENCE_SCORE
        FROM {obj.MFQ_SECTION_CONFIDENCE_TABLE} sc JOIN {obj.MFQ_SECTIONS_TABLE} s ON s.SECTION_ID=sc.SECTION_ID
        WHERE sc.CLAIM_ID='{claim_q}' ORDER BY s.DISPLAY_ORDER, s.SECTION_NAME""",
        query_name="mfq.get_claim_confidence_summary",
    )


def get_llm_evaluation(session, entity_id: str) -> pd.DataFrame:
    entity_q = quote_sql(entity_id)
    return execute_query_df(session, f"SELECT NEEDS_HUMAN_REVIEW,FAITHFULNESS_SCORE,CREATED_AT FROM {obj.LLM_EVALUATION_TABLE} WHERE ENTITY_ID='{entity_q}' ORDER BY CREATED_AT DESC LIMIT 1", query_name="mfq.get_llm_evaluation")
