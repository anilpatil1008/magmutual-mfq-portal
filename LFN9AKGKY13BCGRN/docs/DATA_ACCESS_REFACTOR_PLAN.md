# Data Access Refactor Plan

## Objective
Centralize Snowflake object names, column identifiers, and query execution to reduce blast radius of schema changes.

## Implemented Structure
- `config/snowflake_objects.py`: registry for views/tables used by pages/services.
- `config/column_mappings.py`: reusable column constants.
- `core/snowflake_session.py`: cached shared Snowflake session (`st.cache_resource`).
- `core/query_executor.py`: unified query execution with timing + error handling.
- `repositories/admin_repository.py`, `repositories/notifications_repository.py`: page-level data access moved from UI/service SQL strings.
- `utils/validate_snowflake_objects.py`: startup validation utility.

## Next Iterations
1. Move remaining SQL from `services/claim_service.py` into dedicated repositories (`claims_repository.py`, `mfq_repository.py`, `faculty_repository.py`, `user_repository.py`).
2. Replace all `SELECT *` in claim paths with explicit column lists.
3. Add TTL cache wrappers for claims status lookup and MFQ section/question reads.
4. Wire object validation in startup routing before major pages load.
