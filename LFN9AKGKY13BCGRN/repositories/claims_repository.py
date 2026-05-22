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
        f"""
        SELECT
            c.CLAIM_ID,
            c.PATIENT_NAME,
            c.DRAWER_NAME AS FILE_NUMBER,
            c.CLAIM_STATUS AS STATUS,
            c.UPDATED_AT AS LAST_UPDATED_TS,
            c.FIRST_DOCUMENT_DATE AS DATE_REQUESTED,
            COALESCE(d.DEFENDANT_NAME, 'Unknown Defendant') AS DEFENDANT_NAME
        FROM {obj.MFQ_CLAIMS_TABLE} c
        LEFT JOIN {obj.MFQ_CLAIM_DEFENDANTS_TABLE} d
          ON d.CLAIM_ID = c.CLAIM_ID
         AND COALESCE(d.IS_CURRENT, TRUE) = TRUE
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY c.CLAIM_ID
            ORDER BY COALESCE(d.UPDATED_AT, d.CREATED_AT) DESC
        ) = 1
        """,
        query_name="claims.get_claims_queue",
    )

def get_claim_detail(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(
        session,
        f"""
        SELECT
            c.CLAIM_ID,
            c.PATIENT_NAME,
            c.DRAWER_NAME AS FILE_NUMBER,
            c.FOLDER_NAME,
            c.CLAIM_STATUS AS STATUS,
            c.SYNC_STATUS,
            c.DEFENDANT_STATUS,
            c.MINIMUM_GATE_STATUS,
            c.MINIMUM_GATE_DETAILS,
            c.EMBEDDING_STATUS,
            c.FIRST_DOCUMENT_DATE AS DATE_REQUESTED,
            c.LAST_DOCUMENT_DATE,
            c.SOURCE_DOCUMENT_COUNT,
            c.LAST_SYNCED_AT,
            c.CREATED_AT,
            c.UPDATED_AT AS LAST_UPDATED_TS,
            d.DEFENDANT_ID,
            d.DEFENDANT_NAME,
            d.DEFENDANT_TYPE AS SPECIALTY,
            d.NORMALIZED_DEFENDANT_KEY,
            d.EXTRACTION_STATUS
        FROM {obj.MFQ_CLAIMS_TABLE} c
        LEFT JOIN {obj.MFQ_CLAIM_DEFENDANTS_TABLE} d
          ON d.CLAIM_ID = c.CLAIM_ID
         AND COALESCE(d.IS_CURRENT, TRUE) = TRUE
        WHERE c.CLAIM_ID = '{claim_q}'
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY c.CLAIM_ID
            ORDER BY COALESCE(d.UPDATED_AT, d.CREATED_AT) DESC
        ) = 1
        """,
        query_name="claims.get_claim_detail",
    )


def get_claim_defendants(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT DEFENDANT_ID, CLAIM_ID, DEFENDANT_NAME FROM {obj.MFQ_CLAIM_DEFENDANTS_TABLE} WHERE CLAIM_ID = '{claim_q}'", query_name="claims.get_claim_defendants")


def get_claim_documents(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,DOCUMENT_ID,DOCUMENT_NAME,DOCUMENT_TYPE,CREATED_TS FROM {obj.MFQ_DOCUMENTS_TABLE} WHERE CLAIM_ID = '{claim_q}' ORDER BY CREATED_TS DESC", query_name="claims.get_claim_documents")


def get_assignment_queue(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,ASSIGNMENT_ID,ASSIGNED_TO,ASSIGNED_AT,ASSIGNMENT_STATUS FROM {obj.MFQ_ASSIGNMENT_QUEUE_VIEW} WHERE CLAIM_ID = '{claim_q}' ORDER BY ASSIGNED_AT DESC", query_name="claims.get_assignment_queue")


def get_status_history(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    return execute_query_df(session, f"SELECT CLAIM_ID,STATUS,EVENT_TS,EVENT_NOTE,UPDATED_BY FROM {obj.MFQ_STATUS_HISTORY_TABLE} WHERE CLAIM_ID = '{claim_q}' ORDER BY EVENT_TS DESC", query_name="claims.get_status_history")


def update_claim_status(session, claim_id: str, new_status: str) -> None:
    claim_q = quote_sql(claim_id)
    status_q = quote_sql(new_status)
    session.sql(f"UPDATE {obj.MFQ_CLAIMS_TABLE} SET STATUS = '{status_q}', LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE CLAIM_ID = '{claim_q}'").collect()


def touch_assignment_for_username(session, claim_id: str, assigned_to: str) -> None:
    claim_q = quote_sql(claim_id)
    assigned_q = quote_sql(assigned_to)
    session.sql(f"UPDATE {obj.MFQ_ASSIGNMENTS_TABLE} ca SET LAST_UPDATED_TS = CURRENT_TIMESTAMP() WHERE CLAIM_ID = '{claim_q}' AND ASSIGNED_TO_USER_ID IN (SELECT USER_ID FROM {obj.MFQ_USERS_TABLE} WHERE USERNAME = '{assigned_q}')").collect()
