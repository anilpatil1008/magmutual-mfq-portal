from __future__ import annotations
import pandas as pd
from config import snowflake_objects as obj
from core.query_executor import execute_query_df

def get_assignable_faculty_with_roles(session) -> pd.DataFrame:
    return execute_query_df(session, f"""
    SELECT DISTINCT u.USER_ID,u.USERNAME,COALESCE(NULLIF(u.DISPLAY_NAME, ''), u.USERNAME) AS DISPLAY_NAME
    FROM {obj.MFQ_USERS_TABLE} u
    JOIN {obj.MFQ_USER_ROLES_TABLE} ur ON ur.USER_ID=u.USER_ID AND COALESCE(ur.IS_ACTIVE, TRUE)=TRUE
    JOIN {obj.MFQ_ROLES_TABLE} r ON r.ROLE_ID=ur.ROLE_ID AND COALESCE(r.IS_ACTIVE, TRUE)=TRUE
    WHERE COALESCE(u.IS_ACTIVE, TRUE)=TRUE AND (
      UPPER(COALESCE(r.ROLE_NAME, ''))='MEDICAL FACULTY' OR UPPER(COALESCE(r.ROLE_CODE, '')) IN ('MEDICAL_FACULTY','MEDICAL FACULTY'))
    ORDER BY DISPLAY_NAME
    """, query_name="faculty.get_assignable_with_roles")

def get_assignable_faculty_basic(session) -> pd.DataFrame:
    return execute_query_df(session, f"SELECT USER_ID,USERNAME,COALESCE(NULLIF(DISPLAY_NAME,''),USERNAME) AS DISPLAY_NAME FROM {obj.MFQ_USERS_TABLE} WHERE COALESCE(IS_ACTIVE, TRUE)=TRUE ORDER BY DISPLAY_NAME", query_name="faculty.get_assignable_basic")
