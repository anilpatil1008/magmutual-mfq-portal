# MagMutual MFQ Portal

Streamlit + Snowflake (Snowpark) portal for MFQ claim review workflows.

## Repository layout

- `YUMF5C0V3Q3NRSIZ/streamlit_app.py` – Streamlit entrypoint.
- `YUMF5C0V3Q3NRSIZ/sql/` – Snowflake SQL setup scripts (run in order).

## Snowflake deployment (Snowsight worksheet)

Run these commands in order:

```sql
!source YUMF5C0V3Q3NRSIZ/sql/00_session_context.sql;
!source YUMF5C0V3Q3NRSIZ/sql/01_create_core_objects.sql;
!source YUMF5C0V3Q3NRSIZ/sql/02_create_views.sql;
!source YUMF5C0V3Q3NRSIZ/sql/03_seed_system_config.sql;
!source YUMF5C0V3Q3NRSIZ/sql/04_create_ui_portal_objects.sql;
!source YUMF5C0V3Q3NRSIZ/sql/05_seed_questionnaire.sql;
```

If `!source` is not enabled in your worksheet, open each script file and execute it manually in the same order.

## Streamlit deployment command

From repository root:

```bash
cd YUMF5C0V3Q3NRSIZ
streamlit run streamlit_app.py
```

For Snowflake Native App / Streamlit in Snowflake, upload this project as your app source and ensure the SQL scripts above have been executed in the target database/schema.
