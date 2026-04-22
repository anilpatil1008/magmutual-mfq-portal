from __future__ import annotations

from config.settings import CONFIG
from repositories.base_repository import run_query, esc


def get_user_profile(user_id: str):
    return run_query(f"""
        SELECT USER_ID, USER_NAME, EMAIL, DISPLAY_NAME
        FROM {CONFIG.database}.{CONFIG.schema}.APP_USER
        WHERE USER_ID = '{esc(user_id)}'
    """)


def get_user_roles(user_id: str):
    return run_query(f"""
        SELECT r.ROLE_KEY, r.ROLE_NAME
        FROM {CONFIG.database}.{CONFIG.schema}.APP_USER_ROLE ur
        JOIN {CONFIG.database}.{CONFIG.schema}.APP_ROLE r ON ur.ROLE_ID = r.ROLE_ID
        WHERE ur.USER_ID = '{esc(user_id)}'
        ORDER BY r.ROLE_NAME
    """)
