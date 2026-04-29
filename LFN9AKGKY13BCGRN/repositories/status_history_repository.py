from __future__ import annotations

import pandas as pd

from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql


def get_status_history(session, claim_id: str) -> pd.DataFrame:
    claim_q = quote_sql(claim_id)
    sql = f"SELECT CLAIM_ID,STATUS,EVENT_TS,EVENT_NOTE,UPDATED_BY FROM {obj.MFQ_STATUS_HISTORY_TABLE} WHERE CLAIM_ID='{claim_q}' ORDER BY EVENT_TS DESC"
    return execute_query_df(session, sql, query_name="status_history.get_status_history")
