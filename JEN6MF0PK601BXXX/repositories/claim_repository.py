from __future__ import annotations

from typing import Optional

from config.settings import CONFIG
from repositories.base_repository import run_query, esc, exec_sql


def get_dashboard_metrics():
    return run_query(f"""
        SELECT
            COUNT(*) AS TOTAL_ACTIVE_CLAIMS,
            COUNT_IF(STATUS = 'MFQ Generated') AS MFQ_GENERATED,
            COUNT_IF(STATUS = 'Assigned') AS ASSIGNED,
            COUNT_IF(STATUS = 'Approved') AS APPROVED,
            COUNT_IF(STATUS = 'Rejected') AS REJECTED
        FROM {CONFIG.database}.{CONFIG.schema}.CLAIM
    """)


def get_claim_queue(search_text: str = "", status_filter: Optional[list[str]] = None,
                    priority_filter: Optional[list[str]] = None,
                    confidence_band: str = "All"):
    filters: list[str] = []
    if search_text:
        q = esc(search_text)
        filters.append(f"(FILE_NUMBER ILIKE '%{q}%' OR PATIENT_NAME ILIKE '%{q}%' OR DEFENDANT_NAME ILIKE '%{q}%')")
    if status_filter:
        statuses = ",".join([f"'{esc(x)}'" for x in status_filter])
        filters.append(f"STATUS IN ({statuses})")
    if priority_filter:
        priorities = ",".join([f"'{esc(x)}'" for x in priority_filter])
        filters.append(f"PRIORITY IN ({priorities})")
    if confidence_band == "High":
        filters.append("AI_CONFIDENCE >= 90")
    elif confidence_band == "Medium":
        filters.append("AI_CONFIDENCE BETWEEN 80 AND 89.99")
    elif confidence_band == "Low":
        filters.append("AI_CONFIDENCE < 80")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    return run_query(f"""
        SELECT *
        FROM {CONFIG.database}.{CONFIG.schema}.VW_CLAIM_QUEUE
        {where_clause}
        ORDER BY DATE_REQUESTED DESC, FILE_NUMBER
    """)


def get_claim_header(claim_id: str):
    return run_query(f"""
        SELECT
            c.CLAIM_ID,
            c.FILE_NUMBER,
            c.PATIENT_NAME,
            c.STATUS,
            c.PRIORITY,
            c.DATE_REQUESTED,
            c.AI_CONFIDENCE,
            d.DEFENDANT_ID,
            d.DEFENDANT_NAME,
            d.DEFENDANT_SPECIALTY,
            d.BRIEF_SYNOPSIS,
            d.ALLEGED_INJURY_TERMS,
            d.ALLEGATION_SUMMARY
        FROM {CONFIG.database}.{CONFIG.schema}.CLAIM c
        JOIN {CONFIG.database}.{CONFIG.schema}.CLAIM_DEFENDANT d ON c.CLAIM_ID = d.CLAIM_ID
        WHERE c.CLAIM_ID = '{esc(claim_id)}'
    """)


def approve_claim(claim_id: str) -> None:
    exec_sql(f"""
        UPDATE {CONFIG.database}.{CONFIG.schema}.CLAIM
        SET STATUS = 'Approved'
        WHERE CLAIM_ID = '{esc(claim_id)}'
    """)


def request_regeneration(claim_id: str, user_id: str, reason: str) -> None:
    exec_sql(f"""
        INSERT INTO {CONFIG.database}.{CONFIG.schema}.REGENERATION_LOG
        (REGENERATION_ID, CLAIM_ID, REQUESTED_BY, STATUS, REASON, CREATED_AT)
        VALUES
        (UUID_STRING(), '{esc(claim_id)}', '{esc(user_id)}', 'REQUESTED', '{esc(reason)}', CURRENT_TIMESTAMP())
    """)
