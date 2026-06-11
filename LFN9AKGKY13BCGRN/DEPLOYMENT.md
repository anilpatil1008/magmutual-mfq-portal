# Snowflake Streamlit Deployment Notes

## Dependency model used by this app

- Snowflake Streamlit runtime dependencies are defined in `environment.yml`.
- The runtime is pinned to Python 3.12 because Snowflake packages used by this app (`pandas` and `snowflake-snowpark-python`) are not available for Python 3.11 in Snowflake Streamlit.
- The app is intended to run directly from source (`streamlit_app.py`), not by installing the repository as a local Python package.
- This avoids build-time requirements such as `setuptools`/`wheel` for local project packaging.

## Why the `setuptools>=68, wheel` error happens

If a `pyproject.toml` with a `[build-system]` section exists at deployment root, Snowflake may attempt to build the local source tree as an installable package (`... @ file:///opt/streamlit-runtime`).  
In restricted environments this can fail when PyPI cannot be reached, producing DNS/package-resolution errors.

## External Access Integration (EAI) requirement

If your app still depends on packages that must be fetched from PyPI:

1. `ACCOUNTADMIN` must enable an External Access Integration (EAI) that allows outbound package access.
2. The EAI must be attached to the Streamlit app.
3. DNS + HTTPS egress must allow:
   - `pypi.org`
   - `files.pythonhosted.org`

If all required dependencies are available via Snowflake-supported channels and listed in `environment.yml`, PyPI EAI is typically not required.


## Streamlit source folder mapping

Deploy the app from source folder root (`LFN9AKGKY13BCGRN`) and keep:

- `MAIN_FILE = '/streamlit_app.py'`

A ready-to-run SQL example is provided in `deployment.sql`.
