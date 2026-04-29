from __future__ import annotations
import pandas as pd
from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql

def get_status_values(session):
    return execute_query_df(session, f"SELECT DISTINCT STATUS FROM {obj.MFQ_RECENT_CLAIMS_VIEW} ORDER BY STATUS", query_name="mfq.get_status")

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
