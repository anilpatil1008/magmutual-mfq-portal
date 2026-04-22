from __future__ import annotations

from core.session import get_session
from repositories.base_repository import esc
from config.settings import CONFIG


def approve_claim(claim_id: str) -> None:
    session = get_session()
    if session is None:
        raise RuntimeError("Approve works only inside Streamlit in Snowflake.")

    session.sql(f"""
        UPDATE {CONFIG.database}.{CONFIG.schema}.CLAIM
        SET STATUS = 'Approved'
        WHERE CLAIM_ID = '{esc(claim_id)}'
    """).collect()


def request_regeneration(
    claim_id: str,
    user_id: str,
    reason: str = "User requested regenerate",
) -> None:
    session = get_session()
    if session is None:
        raise RuntimeError("Regenerate works only inside Streamlit in Snowflake.")

    session.sql(f"""
        INSERT INTO {CONFIG.database}.{CONFIG.schema}.REGENERATION_LOG
        (
            REGENERATION_ID,
            CLAIM_ID,
            REQUESTED_BY,
            STATUS,
            REASON,
            CREATED_AT
        )
        VALUES
        (
            UUID_STRING(),
            '{esc(claim_id)}',
            '{esc(user_id)}',
            'REQUESTED',
            '{esc(reason)}',
            CURRENT_TIMESTAMP()
        )
    """).collect()