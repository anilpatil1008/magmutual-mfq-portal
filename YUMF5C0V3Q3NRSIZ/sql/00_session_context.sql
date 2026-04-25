-- Set these values before running the install scripts in Snowsight.
SET APP_DB = 'DEV_DWH';
SET APP_SCHEMA = 'MFQ';
SET APP_STAGE = 'MFQ_CODE_STAGE';
SET APP_WAREHOUSE = 'WH_MFQ';
SET TASK_NAME = 'TSK_MFQ_BATCH';
SET STREAM_NAME = 'STRM_OCR_RESULTS_MFQ';
SET TASK_SCHEDULE = 'USING CRON 0/15 * * * * UTC';

-- Existing OCR source objects.
SET SOURCE_DB = 'DEV_DWH';
SET SOURCE_SCHEMA = 'OCR_EXTRACTION';
SET SOURCE_COMBINED_TABLE_INDEX = 'COMBINED_TABLE_INDEX';
SET SOURCE_DOCUMENT_OCR_RESULTS = 'DOCUMENT_OCR_RESULTS';
SET SOURCE_DOCUMENT_SENTENCES = 'DOCUMENT_SENTENCES';

-- Upload artifacts/mfq_platform_src.zip to:
--   @<APP_DB>.<APP_SCHEMA>.<APP_STAGE>/packages/mfq_platform_src.zip
-- using Snowsight > Catalog > Stage > Upload Files.
