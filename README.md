# MagMutual MFQ Portal (Streamlit in Snowflake)

Enterprise MFQ portal built for **Streamlit in Snowflake** using:
- Streamlit
- Python
- Snowpark `get_active_session()`
- Snowflake tables/views
- Carbon-inspired custom CSS (no React)

## Project structure

```text
streamlit_app.py
components/
  layout.py
  cards.py
  tables.py
  badges.py
  filters.py
  forms.py
pages/
  dashboard.py
  claims.py
  claim_details.py
  reports.py
services/
  snowflake_service.py
styles/
  carbon_like.css
utils/
  constants.py
  helpers.py
sql/
  setup_mfq_portal.sql
```

## Snowflake setup
1. Run `sql/setup_mfq_portal.sql` in your Snowflake worksheet.
2. Create a Streamlit in Snowflake app and upload this repo files.
3. Set the entrypoint to `streamlit_app.py`.

## Notes
- Authentication uses native Snowflake login only.
- Session acquisition uses:

```python
from snowflake.snowpark.context import get_active_session
session = get_active_session()
```

- Claims and MFQ forms are loaded dynamically from `MFQ_CLAIMS_VW` and `MFQ_SECTIONS`.
