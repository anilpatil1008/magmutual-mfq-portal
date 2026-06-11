# Snowflake Streamlit Deployment Notes

## Dependency model used by this app

- Snowflake Streamlit warehouse runtime dependencies are defined in `environment.yml`.
- The runtime is pinned to Python 3.11 because the target Snowflake account reports that `pandas` and `snowflake-snowpark-python` are available for Python 3.11 but not for Python 3.10.
- Use Conda-style pins in `environment.yml` (`python=3.11`, not `python==3.11` or `python==3.10`). Snowflake treats `python==...` as an invalid package request and can raise `Packages not found: python==3.10`.
- The app is intended to run directly from source (`streamlit_app.py`), not by installing the repository as a local Python package.
- This avoids build-time requirements such as `setuptools`/`wheel` for local project packaging.

## Fixing the `Packages not found: python==3.10` startup error

1. Ensure the source folder staged for the Streamlit app contains the updated `environment.yml` at its root.
2. In Snowsight, open the app editor and refresh the Packages panel. Remove any Python entry shown as `python==3.10`, then select Python 3.11.
3. If you deploy from a stage, clear stale files from the stage before uploading the app again so an old dependency file cannot be reused.
4. Recreate or alter the Streamlit app and publish a new live version.

A valid warehouse-runtime dependency file for this app is:

```yaml
name: sf_env
channels:
  - snowflake
dependencies:
  - python=3.11
  - streamlit=1.48.0
  - pandas=2.*
  - snowflake-snowpark-python
```

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
