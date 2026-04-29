from __future__ import annotations

from config import snowflake_objects as obj
from core.query_executor import execute_query_df
from services.snowflake_service import quote_sql


def get_assignment_username(session, faculty_user_id: str):
    user_id_q = quote_sql(faculty_user_id)
    return execute_query_df(
        session,
        f"SELECT USERNAME FROM {obj.MFQ_USERS_TABLE} WHERE USER_ID = '{user_id_q}' LIMIT 1",
        query_name="assignment.get_assignment_username",
    )


def insert_assignment(session, claim_id: str, faculty_user_id: str, assigned_by_username: str) -> None:
    claim_q = quote_sql(claim_id)
    faculty_user_id_q = quote_sql(faculty_user_id)
    assigned_by_q = quote_sql(assigned_by_username)
    session.sql(
        f"""
        INSERT INTO {obj.MFQ_ASSIGNMENTS_TABLE} (
          ASSIGNMENT_ID, CLAIM_ID, ASSIGNED_TO_USER_ID, ASSIGNED_BY_USER_ID, ASSIGNMENT_STATUS, PRIORITY, ASSIGNED_AT, LAST_UPDATED_TS
        )
        SELECT
          CONCAT('ASG-', REPLACE(UUID_STRING(), '-', '')),
          '{claim_q}',
          '{faculty_user_id_q}',
          COALESCE((SELECT USER_ID FROM {obj.MFQ_USERS_TABLE} WHERE UPPER(USERNAME) = UPPER('{assigned_by_q}') LIMIT 1), '{faculty_user_id_q}'),
          'ASSIGNED', 'Medium', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
        """
    ).collect()


def get_latest_assignment_id(session, claim_id: str, faculty_user_id: str):
    claim_q = quote_sql(claim_id)
    faculty_user_id_q = quote_sql(faculty_user_id)
    return execute_query_df(
        session,
        f"""
        SELECT ASSIGNMENT_ID FROM {obj.MFQ_ASSIGNMENTS_TABLE}
        WHERE CLAIM_ID = '{claim_q}' AND ASSIGNED_TO_USER_ID = '{faculty_user_id_q}'
        ORDER BY ASSIGNED_AT DESC, LAST_UPDATED_TS DESC LIMIT 1
        """,
        query_name="assignment.get_latest_assignment_id",
    )


def insert_assignment_sections(session, assignment_id: str, claim_id: str, faculty_user_id: str, section_ids: list[str]) -> None:
    assignment_id_q = quote_sql(assignment_id)
    claim_q = quote_sql(claim_id)
    faculty_user_id_q = quote_sql(faculty_user_id)
    values_sql = ",\n          ".join(
        [
            f"(CONCAT('ASSEC-', REPLACE(UUID_STRING(), '-', '')), '{assignment_id_q}', '{claim_q}', '{quote_sql(str(section_id))}', '{faculty_user_id_q}', 'ASSIGNED', CURRENT_TIMESTAMP())"
            for section_id in section_ids
        ]
    )
    session.sql(
        f"""
        INSERT INTO {obj.MFQ_ASSIGNMENT_SECTIONS_TABLE} (
          ASSIGNMENT_SECTION_ID, ASSIGNMENT_ID, CLAIM_ID, SECTION_ID, ASSIGNED_TO_USER_ID, ASSIGNMENT_STATUS, ASSIGNED_AT
        )
        SELECT * FROM VALUES {values_sql}
        """
    ).collect()


def update_claim_for_assignment(session, claim_id: str, assigned_username: str | None, claim_cols: set[str]) -> None:
    claim_q = quote_sql(claim_id)
    status_update_sql = f"UPDATE {obj.MFQ_CLAIMS_TABLE} SET STATUS = 'Assigned'"
    if "LAST_UPDATED_TS" in claim_cols:
        status_update_sql += ", LAST_UPDATED_TS = CURRENT_TIMESTAMP()"
    if assigned_username and "ASSIGNED_TO" in claim_cols:
        status_update_sql += f", ASSIGNED_TO = '{quote_sql(assigned_username)}'"
    status_update_sql += f" WHERE CLAIM_ID = '{claim_q}'"
    session.sql(status_update_sql).collect()


def get_editable_section_ids(session, claim_id: str, username: str):
    claim_q = quote_sql(claim_id)
    user_q = quote_sql(username)
    return execute_query_df(
        session,
        f"""
        SELECT DISTINCT ase.SECTION_ID
        FROM {obj.MFQ_ASSIGNMENT_SECTIONS_TABLE} ase
        JOIN {obj.MFQ_USERS_TABLE} u ON u.USER_ID = ase.ASSIGNED_TO_USER_ID
        WHERE ase.CLAIM_ID = '{claim_q}' AND UPPER(u.USERNAME) = UPPER('{user_q}')
        """,
        query_name="assignment.get_editable_section_ids",
    )
