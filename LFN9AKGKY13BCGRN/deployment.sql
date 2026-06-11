-- Deploy from the LFN9AKGKY13BCGRN source folder so environment.yml sits at
-- the root of the Streamlit source location next to streamlit_app.py.
--
-- If this stage was used before, clear stale dependency files first; otherwise
-- Snowflake can keep resolving an old environment.yml/requirements.txt that
-- still contains an invalid package spec such as python==3.11.
CREATE OR REPLACE STAGE MAGMUTUAL_MFQ_APP.PUBLIC.MFQ_APP_STAGE;

-- Upload the contents of LFN9AKGKY13BCGRN/ to @MFQ_APP_STAGE before running the
-- CREATE STREAMLIT statement. The staged root must include:
--   - streamlit_app.py
--   - environment.yml
--   - components/, pages/, repositories/, services/, utils/, styles/

CREATE OR REPLACE STREAMLIT MAGMUTUAL_MFQ_APP.PUBLIC.MFQ_V1
  ROOT_LOCATION = '@MAGMUTUAL_MFQ_APP.PUBLIC.MFQ_APP_STAGE'
  MAIN_FILE = '/streamlit_app.py'
  QUERY_WAREHOUSE = COMPUTE_WH;

-- Publish the newly-created version when deploying through SQL automation.
ALTER STREAMLIT MAGMUTUAL_MFQ_APP.PUBLIC.MFQ_V1 ADD LIVE VERSION FROM LAST;
