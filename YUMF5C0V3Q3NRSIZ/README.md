# MagMutual MFQ Enterprise Portal

Streamlit + Snowflake (Snowpark) portal for MFQ claim review workflows.

## App folder layout

This folder is the complete Snowflake Streamlit app source:

- `streamlit_app.py`
- `components/`
- `pages/`
- `services/`
- `styles/carbon_like.css`
- `sql/00_session_context.sql` through `sql/07_validation_queries.sql`

## SQL deployment order (Snowsight)

Run in this exact order:

```sql
!source YUMF5C0V3Q3NRSIZ/sql/00_session_context.sql;
!source YUMF5C0V3Q3NRSIZ/sql/01_create_core_objects.sql;
!source YUMF5C0V3Q3NRSIZ/sql/02_create_views.sql;
!source YUMF5C0V3Q3NRSIZ/sql/03_seed_system_config.sql;
!source YUMF5C0V3Q3NRSIZ/sql/04_create_ui_objects.sql;
!source YUMF5C0V3Q3NRSIZ/sql/05_seed_questionnaire.sql;
!source YUMF5C0V3Q3NRSIZ/sql/06_seed_demo_data.sql;
!source YUMF5C0V3Q3NRSIZ/sql/07_validation_queries.sql;
```

## Local run

```bash
cd YUMF5C0V3Q3NRSIZ
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Troubleshooting: `SyntaxError` on line 1 in Snowflake runtime

If you see an error similar to:

```text
SyntaxError: invalid syntax
```

with an object name prefix (for example `...MFQ_SECTIONSfrom ...`) on line 1, the deployed
`streamlit_app.py` has been corrupted during upload/paste. Re-upload the project source and confirm
the first line of `streamlit_app.py` starts cleanly with:

```python
import streamlit as st
```
