-- Run in your target database/schema for Streamlit in Snowflake

CREATE OR REPLACE TABLE MFQ_CLAIMS (
  CLAIM_ID STRING,
  PATIENT_NAME STRING,
  DEFENDANT_NAME STRING,
  FILE_NUMBER STRING,
  SPECIALTY STRING,
  DATE_REQUESTED DATE,
  CONTACT_DETAILS STRING,
  STATUS STRING,
  PRIORITY STRING,
  AI_CONFIDENCE NUMBER(5,2),
  ASSIGNED_TO STRING,
  APPROVED_BY STRING,
  HAS_NEW_MFQ_VERSION BOOLEAN,
  RECORDS_SUMMARY STRING,
  MEDCRON_TEXT STRING,
  LEGAL_MEMO_TEXT STRING,
  LAST_UPDATED_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE MFQ_SECTIONS (
  CLAIM_ID STRING,
  SECTION_ORDER NUMBER,
  SECTION_NAME STRING,
  QUESTION_ORDER NUMBER,
  QUESTION_ID STRING,
  QUESTION_TEXT STRING,
  ANSWER_TEXT STRING,
  AI_CONFIDENCE NUMBER(5,2),
  SECTION_CONFIDENCE NUMBER(5,2),
  IS_EDITABLE BOOLEAN DEFAULT TRUE
);

CREATE OR REPLACE VIEW MFQ_CLAIMS_VW AS
SELECT * FROM MFQ_CLAIMS;

INSERT INTO MFQ_CLAIMS (CLAIM_ID,PATIENT_NAME,DEFENDANT_NAME,FILE_NUMBER,SPECIALTY,DATE_REQUESTED,CONTACT_DETAILS,STATUS,PRIORITY,AI_CONFIDENCE,ASSIGNED_TO,APPROVED_BY,HAS_NEW_MFQ_VERSION,RECORDS_SUMMARY,MEDCRON_TEXT,LEGAL_MEMO_TEXT)
VALUES
('CLM-1001','John Carter','Dr. Alice Brown','FN-2026-1001','Orthopedics','2026-04-18','john.carter@email.com | +1-555-1001','MFQ Generated','High',87.5,'FACULTY_1',NULL,TRUE,'Patient post-op recovery summary...','Chronology events for claim 1001...','Legal memo summary for 1001...'),
('CLM-1002','Emma Davis','City Hospital','FN-2026-1002','Cardiology','2026-04-20','emma.davis@email.com | +1-555-1002','Assigned','Critical',93.2,'FACULTY_1',NULL,FALSE,'Cardiac records summary...','Chronology for claim 1002...','Legal memo 1002...'),
('CLM-1003','Liam Miller','Dr. Patel','FN-2026-1003','Neurology','2026-04-14','liam.miller@email.com | +1-555-1003','Approved','Medium',91.1,'FACULTY_2','FACULTY_2',FALSE,'Neurology record summary...','Chronology for claim 1003...','Legal memo 1003...'),
('CLM-1004','Sophia Wilson','County Medical Center','FN-2026-1004','Emergency Medicine','2026-04-12','sophia.w@email.com | +1-555-1004','Rejected','Low',75.8,'FACULTY_3',NULL,TRUE,'ER records summary...','Chronology for claim 1004...','Legal memo 1004...');

INSERT INTO MFQ_SECTIONS (CLAIM_ID,SECTION_ORDER,SECTION_NAME,QUESTION_ORDER,QUESTION_ID,QUESTION_TEXT,ANSWER_TEXT,AI_CONFIDENCE,SECTION_CONFIDENCE,IS_EDITABLE)
VALUES
('CLM-1001',1,'Patient History',1,'Q-1001-1','What is the chief complaint?','Persistent knee pain after surgery.',92,89,TRUE),
('CLM-1001',1,'Patient History',2,'Q-1001-2','Any prior related condition?','History of ACL tear in 2023.',84,89,TRUE),
('CLM-1001',2,'Treatment Review',1,'Q-1001-3','Was treatment protocol followed?','Most steps were followed; missing physiotherapy note.',78,81,TRUE),
('CLM-1002',1,'Cardiac Summary',1,'Q-1002-1','ECG interpretation?','Normal sinus rhythm, occasional PVC.',95,93,FALSE),
('CLM-1002',2,'Medication Review',1,'Q-1002-2','Any contraindications found?','No significant contraindications.',90,92,TRUE),
('CLM-1003',1,'Neuro Status',1,'Q-1003-1','Neurological deficits?','Mild intermittent numbness reported.',89,91,TRUE),
('CLM-1004',1,'ER Intake',1,'Q-1004-1','Triage completeness?','Incomplete vitals documentation.',72,76,TRUE);

-- Aggregation queries used by reports page
-- Claims by status
SELECT STATUS, COUNT(*) AS COUNT FROM MFQ_CLAIMS_VW GROUP BY STATUS;

-- Claims by priority
SELECT PRIORITY, COUNT(*) AS COUNT FROM MFQ_CLAIMS_VW GROUP BY PRIORITY;

-- Faculty performance
SELECT ASSIGNED_TO, COUNT(*) AS TOTAL,
       SUM(IFF(STATUS='Approved',1,0)) AS APPROVED
FROM MFQ_CLAIMS_VW
GROUP BY ASSIGNED_TO;

-- Claims by specialty
SELECT SPECIALTY, COUNT(*) AS COUNT FROM MFQ_CLAIMS_VW GROUP BY SPECIALTY;
