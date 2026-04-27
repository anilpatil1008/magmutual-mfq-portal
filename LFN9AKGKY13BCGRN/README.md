# MagMutual MFQ Enterprise Portal

Enterprise Streamlit in Snowflake application for claim intake, MFQ workspace, assignment workflows, notifications, reports, and admin RBAC.

## Required SQL execution order

Run these scripts in order:

1. `sql/00_session_context.sql`
2. `sql/01_create_core_objects.sql`
3. `sql/05_seed_questionnaire.sql`
4. `sql/04_create_ui_objects.sql`
5. `sql/00_clean_demo_data.sql`
6. `sql/06_seed_demo_data.sql`
7. `sql/07_validation_queries.sql`

## Snowflake Streamlit deployment

```sql
CREATE OR REPLACE STAGE MAGMUTUAL_MFQ_APP.PUBLIC.MFQ_APP_STAGE;

CREATE OR REPLACE STREAMLIT MAGMUTUAL_MFQ_APP.PUBLIC.MAGMUTUAL_MFQ_ENTERPRISE_PORTAL
  ROOT_LOCATION = '@MAGMUTUAL_MFQ_APP.PUBLIC.MFQ_APP_STAGE'
  MAIN_FILE = '/LFN9AKGKY13BCGRN/streamlit_app.py'
  QUERY_WAREHOUSE = COMPUTE_WH;
```

## Runtime notes

- Uses Snowflake active session via `get_active_session()`.
- Uses `environment.yml` for Snowflake Streamlit package resolution.
- CSS is loaded safely with `pathlib`.
- See `DEPLOYMENT.md` for packaging/EAI troubleshooting guidance.
