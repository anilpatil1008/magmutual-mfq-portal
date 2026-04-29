from __future__ import annotations

import pandas as pd

from config import column_mappings as col
from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql


def get_claim_confidence_summary(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    sql = f"""
    SELECT sc.{col.CLAIM_ID}, sc.{col.SECTION_ID}, s.SECTION_NAME, s.DISPLAY_ORDER AS SECTION_ORDER,
           sc.{col.CONFIDENCE_SCORE}
    FROM {obj.MFQ_SECTION_CONFIDENCE_TABLE} sc
    JOIN {obj.MFQ_SECTIONS_TABLE} s ON s.{col.SECTION_ID} = sc.{col.SECTION_ID}
    WHERE sc.{col.CLAIM_ID} = '{claim_q}'
    ORDER BY s.DISPLAY_ORDER
    """
    return execute_query_df(session, sql, query_name="confidence.get_claim_confidence_summary")


def get_section_confidence(session, claim_id: str, section_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    section_q = quote_sql(section_id)
    sql = f"SELECT {col.CLAIM_ID},{col.SECTION_ID},{col.CONFIDENCE_SCORE} FROM {obj.MFQ_SECTION_CONFIDENCE_TABLE} WHERE {col.CLAIM_ID}='{claim_q}' AND {col.SECTION_ID}='{section_q}'"
    return execute_query_df(session, sql, query_name="confidence.get_section_confidence")
