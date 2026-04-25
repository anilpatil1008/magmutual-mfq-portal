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
# MagMutual MFQ Enterprise Portal

Production-style Streamlit in Snowflake prototype for Medical Faculty Questionnaire (MFQ) operations.

## Architecture

- `streamlit_app.py`: app entry point + page routing.
- `components/`: reusable UI modules (layout, cards, tables, badges, notifications).
- `pages/`: role-based page modules (dashboard, claims, claim details, reports, admin).
- `services/`: Snowflake session, RBAC, claims, dashboard, notification services.
- `styles/carbon_like.css`: IBM Carbon-inspired enterprise styling.
- `sql/04_create_ui_objects.sql`: UI tables/views.
- `sql/06_seed_demo_data.sql`: demo seed data.

## Snowflake Runtime Notes

This app is designed for **Streamlit in Snowflake** and uses:

```python
from snowflake.snowpark.context import get_active_session
```

The code expects these UI objects to exist:

- `MFQ_CLAIMS_VW`
- `MFQ_SECTIONS_VW`
- `MFQ_NOTIFICATIONS_VW`
- `MFQ_APP_USERS`
- `MFQ_ROLE_PAGE_ACCESS`
- `MFQ_ASSIGNMENT_RULES`
- `MFQ_NOTIFICATIONS`

Run SQL in order after core scripts:

1. `sql/04_create_ui_objects.sql`
2. `sql/06_seed_demo_data.sql`

## Local Development

```bash
pip install -e .
streamlit run streamlit_app.py
```

For local execution outside Snowflake, mock `get_active_session()` or run inside a Snowflake-native Streamlit app.
