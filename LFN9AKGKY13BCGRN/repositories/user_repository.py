from __future__ import annotations
from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql

def get_user_by_id(session, user_id: str):
    q=quote_sql(user_id)
    return execute_query_df(session, f"SELECT USERNAME FROM {obj.MFQ_USERS_TABLE} WHERE USER_ID='{q}' LIMIT 1", query_name="user.get_by_id")
