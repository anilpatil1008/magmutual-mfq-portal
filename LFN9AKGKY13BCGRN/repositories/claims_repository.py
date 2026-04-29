from __future__ import annotations

import pandas as pd

from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql


def object_exists(session, object_name: str) -> bool:
    object_q = quote_sql(object_name.upper())
    df = execute_query_df(
        session,
        f"""
        SELECT 1 AS FOUND FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = CURRENT_SCHEMA() AND TABLE_NAME = '{object_q}'
        UNION ALL
        SELECT 1 AS FOUND FROM INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_SCHEMA = CURRENT_SCHEMA() AND TABLE_NAME = '{object_q}'
        LIMIT 1
        """,
        query_name=f"claims.object_exists.{object_name}",
    )
    return not df.empty


def table_columns(session, table_name: str) -> set[str]:
    if not object_exists(session, table_name):
        return set()
    table_q = quote_sql(table_name.upper())
    df = execute_query_df(
        session,
        f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = CURRENT_SCHEMA() AND TABLE_NAME = '{table_q}'",
        query_name=f"claims.table_columns.{table_name}",
    )
    return {str(v).upper() for v in df.get("COLUMN_NAME", pd.Series(dtype=str)).dropna().tolist()}


def get_claims_queue(session) -> pd.DataFrame:
    return execute_query_df(
        session,
        f"""SELECT CLAIM_ID,PATIENT_NAME,DEFENDANT_NAME,FILE_NUMBER,STATUS,PRIORITY,ASSIGNED_TO,LAST_UPDATED_TS,DATE_REQUESTED FROM {obj.MFQ_RECENT_CLAIMS_VIEW}""",
        query_name="claims.get_claims_queue",
    )

def get_claim_detail(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT * FROM {obj.MFQ_CLAIM_DETAIL_VIEW} WHERE CLAIM_ID = '{claim_q}'", query_name="claims.get_claim_detail")
