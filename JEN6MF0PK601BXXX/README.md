# MagMutual MFQ Portal - Enterprise Streamlit Structure

This package provides a maintainable Streamlit-in-Snowflake starter structure for the MFQ portal.

## Folder layout

- `streamlit_app.py` - app entry and page routing
- `config/` - static configuration
- `core/` - app state, constants, session helpers, utilities
- `repositories/` - Snowflake data access only
- `services/` - business logic
- `components/` - reusable UI parts
- `pages/` - page composition
- `styles/` - central theme and CSS

## Run inside Snowflake

1. Create a Streamlit app in Snowsight.
2. Upload the `app/` folder files into the app project.
3. Ensure the SQL objects and seed data already exist in:
   - `MAGMUTUAL_MFQ_APP.PORTAL`
4. Open `streamlit_app.py` as the entry file.
5. Run the app.

## Why this is maintainable

- SQL is separated from UI.
- Business rules are separated from page rendering.
- Reusable components reduce repeated code.
- Page files stay smaller and easier to extend.
- Theme and CSS are centralized.

## Suggested next improvements

- add audit trail page
- add faculty assignment modal / page
- add notification read/unread update
- add report filters and exports
- replace direct writes with stored procedures if needed
- add unit tests for services and repositories
