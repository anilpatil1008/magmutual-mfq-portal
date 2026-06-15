# MagMutual MFQ Enterprise Portal

Production-style Streamlit in Snowflake prototype for Medical Faculty Questionnaire (MFQ) operations.

## Repository layout

- `streamlit_app.py`: app entry point + page routing.
- `environment.yml`: Snowflake Streamlit runtime dependency manifest.
- `pyproject.toml`: Local/project Python package metadata.
- `components/`: reusable UI modules.
- `pages/`: role-based page modules.
- `services/`: Snowflake session, RBAC, claims, dashboard, and notification services.
- `styles/`: UI styling.
- `sql/`: Snowflake setup/seed scripts.
- `docs/`: project documentation.

## Snowflake deployment (Snowsight worksheet)

Run these commands in order:

```sql
!source sql/00_session_context.sql;
!source sql/01_create_core_objects.sql;
!source sql/02_create_views.sql;
!source sql/03_seed_system_config.sql;
!source sql/04_create_ui_objects.sql;
!source sql/05_seed_questionnaire.sql;
```

Then seed demo data as needed:

```sql
!source sql/06_seed_demo_data.sql;
```

## Local development

Use Python 3.11 locally to match the supported Snowflake Streamlit warehouse runtime configured in `environment.yml`.

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Optional local Snowflake authentication storage

For local development only, Snowflake's connector can persist browser-auth tokens more securely when the optional secure local storage extra is installed:

```bash
pip install "snowflake-connector-python[secure-local-storage]"
```

Do not add this extra to the Snowflake Streamlit deployment dependencies unless the target runtime explicitly supports it.
