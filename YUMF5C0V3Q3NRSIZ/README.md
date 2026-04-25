# MagMutual MFQ Portal

Streamlit + Snowflake (Snowpark) portal for MFQ claim review workflows.

## Repository layout

- `streamlit_app.py` – Streamlit entrypoint.
- `sql/` – Snowflake SQL setup scripts (run in order).

## Snowflake deployment (Snowsight worksheet)

Run these commands in order:

```sql
!source sql/00_session_context.sql;
!source sql/01_create_core_objects.sql;
!source sql/02_create_views.sql;
!source sql/03_seed_system_config.sql;
!source sql/04_create_ui_objects.sql;
!source sql/05_seed_questionnaire.sql;
!source sql/06_seed_demo_data.sql;
!source sql/07_validation_queries.sql;
```

If `!source` is not enabled in your worksheet, open each script file and execute it manually in the same order.

## Local run

```bash
streamlit run streamlit_app.py
```

## Streamlit in Snowflake

Use this folder (`YUMF5C0V3Q3NRSIZ`) as the app root/source location when creating the Snowflake Streamlit app.
