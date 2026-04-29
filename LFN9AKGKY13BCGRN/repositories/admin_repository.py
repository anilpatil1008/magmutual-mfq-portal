from __future__ import annotations

from core.query_executor import execute_query_df
from config import snowflake_objects as obj


def get_users_with_roles(session):
    return execute_query_df(
        session,
        f"""
        SELECT u.USERNAME, u.DISPLAY_NAME, u.IS_ACTIVE, r.ROLE_NAME AS APP_ROLE
        FROM {obj.APP_USER_TABLE} u
        LEFT JOIN {obj.APP_USER_ROLE_TABLE} ur ON ur.USER_ID = u.USER_ID AND ur.IS_ACTIVE = TRUE
        LEFT JOIN {obj.APP_ROLE_TABLE} r ON r.ROLE_ID = ur.ROLE_ID
        ORDER BY u.USERNAME
        """,
        query_name="admin.get_users_with_roles",
    )


def get_role_permissions(session):
    return execute_query_df(
        session,
        f"""
        SELECT r.ROLE_NAME, p.PERMISSION_CODE, p.PERMISSION_NAME, rp.IS_ACTIVE
        FROM {obj.APP_ROLE_PERMISSION_TABLE} rp
        JOIN {obj.APP_ROLE_TABLE} r ON r.ROLE_ID = rp.ROLE_ID
        JOIN {obj.APP_PERMISSION_TABLE} p ON p.PERMISSION_ID = rp.PERMISSION_ID
        ORDER BY r.ROLE_NAME, p.PERMISSION_CODE
        """,
        query_name="admin.get_role_permissions",
    )


def get_assignment_queue(session):
    return execute_query_df(
        session,
        f"SELECT * FROM {obj.MFQ_ASSIGNMENT_QUEUE_VIEW} ORDER BY ASSIGNED_AT DESC",
        query_name="admin.get_assignment_queue",
    )
