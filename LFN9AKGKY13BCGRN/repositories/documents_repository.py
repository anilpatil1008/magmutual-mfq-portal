from __future__ import annotations

import pandas as pd

from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql


def get_claim_documents(session, claim_id: str) -> pd.DataFrame:
    q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,DOCUMENT_ID,DOCUMENT_NAME,DOCUMENT_TYPE,CREATED_TS FROM {obj.MFQ_DOCUMENTS_TABLE} WHERE CLAIM_ID='{q}' ORDER BY CREATED_TS DESC", query_name="documents.get_claim_documents")


def get_medcron_summary(session, claim_id: str) -> pd.DataFrame:
    q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,SUMMARY_TEXT,GENERATED_TS FROM {obj.MFQ_MEDCRON_SUMMARY_TABLE} WHERE CLAIM_ID='{q}' ORDER BY GENERATED_TS DESC LIMIT 1", query_name="documents.get_medcron_summary")


def get_legal_memo(session, claim_id: str) -> pd.DataFrame:
    q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,SUMMARY_TEXT,GENERATED_TS FROM {obj.MFQ_LEGAL_MEMO_TABLE} WHERE CLAIM_ID='{q}' ORDER BY GENERATED_TS DESC LIMIT 1", query_name="documents.get_legal_memo")


def get_record_summary(session, claim_id: str) -> pd.DataFrame:
    q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,SUMMARY_TEXT,GENERATED_TS FROM {obj.MFQ_RECORD_SUMMARY_TABLE} WHERE CLAIM_ID='{q}' ORDER BY GENERATED_TS DESC LIMIT 1", query_name="documents.get_record_summary")
