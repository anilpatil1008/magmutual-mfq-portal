from __future__ import annotations

import pandas as pd

from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql


def get_llm_evaluation(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    sql = f"SELECT ENTITY_ID, NEEDS_HUMAN_REVIEW, FAITHFULNESS_SCORE, CREATED_AT FROM {obj.LLM_EVALUATION_TABLE} WHERE ENTITY_ID='{claim_q}' ORDER BY CREATED_AT DESC LIMIT 1"
    return execute_query_df(session, sql, query_name="evaluation.get_llm_evaluation")


def get_llm_evaluation_by_section(session, claim_id: str, section_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    section_q = quote_sql(section_id)
    sql = f"SELECT ENTITY_ID, SECTION_ID, NEEDS_HUMAN_REVIEW, FAITHFULNESS_SCORE, CREATED_AT FROM {obj.LLM_EVALUATION_TABLE} WHERE ENTITY_ID='{claim_q}' AND SECTION_ID='{section_q}' ORDER BY CREATED_AT DESC LIMIT 1"
    return execute_query_df(session, sql, query_name="evaluation.get_llm_evaluation_by_section")
