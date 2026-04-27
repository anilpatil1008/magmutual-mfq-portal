# MagMutual MFQ Portal

Streamlit + Snowflake (Snowpark) portal for MFQ claim review workflows.

## Repository layout

- `LFN9AKGKY13BCGRN/streamlit_app.py` – Streamlit entrypoint.
- `LFN9AKGKY13BCGRN/sql/` – Snowflake SQL setup scripts (run in order).

## Snowflake deployment (Snowsight worksheet)

Run these commands in order:

```sql
!source LFN9AKGKY13BCGRN/sql/00_session_context.sql;
!source LFN9AKGKY13BCGRN/sql/01_create_core_objects.sql;
!source LFN9AKGKY13BCGRN/sql/02_create_views.sql;
!source LFN9AKGKY13BCGRN/sql/03_seed_system_config.sql;
!source LFN9AKGKY13BCGRN/sql/04_create_ui_objects.sql;
!source LFN9AKGKY13BCGRN/sql/05_seed_questionnaire.sql;
```

If `!source` is not enabled in your worksheet, open each script file and execute it manually in the same order.

## Streamlit deployment command

From repository root:

```bash
cd LFN9AKGKY13BCGRN
pip install -r requirements.txt
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
pip install -r LFN9AKGKY13BCGRN/requirements.txt
streamlit run streamlit_app.py
```

For local execution outside Snowflake, mock `get_active_session()` or run inside a Snowflake-native Streamlit app.

## Snowflake packaging behavior and fix

- Deploy this app as source code (not as an installable Python project package).
- Runtime dependency resolution for Streamlit in Snowflake should come from `LFN9AKGKY13BCGRN/environment.yml`.
- The root `pyproject.toml` build configuration was removed so Snowflake does not attempt to build and install `LFN9AKGKY13BCGRN @ file:///opt/streamlit-runtime`.

## Package install troubleshooting (PyPI DNS / EAI)

If installation fails with an error similar to:

```text
Failed to fetch: https://pypi.org/simple/pandas/
... dns error ... Name does not resolve
```

the runtime environment cannot resolve or reach `pypi.org`.

### What this usually means

- In managed/sandbox environments, **External Access Integration (EAI)** (or equivalent outbound network access) is not enabled.
- DNS is blocked or unavailable for public package hosts.

### How to fix

1. Have `ACCOUNTADMIN` create/enable an External Access Integration (EAI) for package downloads.
2. Attach that EAI to the Streamlit object deployment.
3. Allow DNS + HTTPS egress to package domains such as:
   - `pypi.org`
   - `files.pythonhosted.org`
4. Retry installation.

If all required packages are available through Snowflake-supported channels in `environment.yml`, no PyPI EAI is required.

### Quick validation commands

```bash
python -c "import socket; print(socket.gethostbyname('pypi.org'))"
python -m pip install --upgrade pip
python -m pip install pandas
```

If DNS lookup fails in step 1, this is an environment/network policy issue (not a `pip` or `pandas` issue).
