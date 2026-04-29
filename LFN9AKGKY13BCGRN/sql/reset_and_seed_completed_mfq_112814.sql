-- DEV/TEST ONLY: Reset and reseed completed MFQ data for file 112814
-- Do NOT run in PROD.

/* ============================================================================
   1) Environment setup
============================================================================ */
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE COMPUTE_WH;
USE DATABASE MAGMUTUAL_MFQ_APP;
USE SCHEMA PUBLIC;

/* ============================================================================
   2) Safety backup before delete
============================================================================ */
SET TARGET_FILE_NUMBER = '112814';

CREATE TABLE IF NOT EXISTS BACKUP_MFQ_CLAIMS_112814 AS
SELECT c.*
FROM MFQ_CLAIMS c
WHERE c.FILE_NUMBER = $TARGET_FILE_NUMBER;

CREATE TABLE IF NOT EXISTS BACKUP_MFQ_CLAIM_DEFENDANTS_112814 AS
SELECT d.*
FROM MFQ_CLAIM_DEFENDANTS d
JOIN MFQ_CLAIMS c ON c.CLAIM_ID = d.CLAIM_ID
WHERE c.FILE_NUMBER = $TARGET_FILE_NUMBER;

CREATE TABLE IF NOT EXISTS BACKUP_MFQ_ANSWERS_112814 AS
SELECT a.*
FROM MFQ_ANSWERS a
JOIN MFQ_CLAIMS c ON c.CLAIM_ID = a.CLAIM_ID
WHERE c.FILE_NUMBER = $TARGET_FILE_NUMBER;

CREATE TABLE IF NOT EXISTS BACKUP_MFQ_QUESTION_CONFIDENCE_112814 AS
SELECT qc.*
FROM MFQ_QUESTION_CONFIDENCE qc
JOIN MFQ_CLAIMS c ON c.CLAIM_ID = qc.CLAIM_ID
WHERE c.FILE_NUMBER = $TARGET_FILE_NUMBER;

CREATE TABLE IF NOT EXISTS BACKUP_MFQ_STATUS_HISTORY_112814 AS
SELECT sh.*
FROM MFQ_STATUS_HISTORY sh
JOIN MFQ_CLAIMS c ON c.CLAIM_ID = sh.CLAIM_ID
WHERE c.FILE_NUMBER = $TARGET_FILE_NUMBER;

CREATE TABLE IF NOT EXISTS BACKUP_MFQ_ASSIGNMENTS_112814 AS
SELECT a.*
FROM MFQ_ASSIGNMENTS a
JOIN MFQ_CLAIMS c ON c.CLAIM_ID = a.CLAIM_ID
WHERE c.FILE_NUMBER = $TARGET_FILE_NUMBER;

CREATE TABLE IF NOT EXISTS BACKUP_MFQ_ASSIGNMENT_SECTIONS_112814 AS
SELECT s.*
FROM MFQ_ASSIGNMENT_SECTIONS s
JOIN MFQ_CLAIMS c ON c.CLAIM_ID = s.CLAIM_ID
WHERE c.FILE_NUMBER = $TARGET_FILE_NUMBER;

CREATE TABLE IF NOT EXISTS BACKUP_MFQ_DOCUMENTS_112814 AS
SELECT d.*
FROM MFQ_DOCUMENTS d
JOIN MFQ_CLAIMS c ON c.CLAIM_ID = d.CLAIM_ID
WHERE c.FILE_NUMBER = $TARGET_FILE_NUMBER;

CREATE TABLE IF NOT EXISTS BACKUP_MFQ_RECORD_SUMMARY_112814 AS
SELECT r.*
FROM MFQ_RECORD_SUMMARY r
JOIN MFQ_CLAIMS c ON c.CLAIM_ID = r.CLAIM_ID
WHERE c.FILE_NUMBER = $TARGET_FILE_NUMBER;

CREATE TABLE IF NOT EXISTS BACKUP_MFQ_MEDCRON_SUMMARY_112814 AS
SELECT m.*
FROM MFQ_MEDCRON_SUMMARY m
JOIN MFQ_CLAIMS c ON c.CLAIM_ID = m.CLAIM_ID
WHERE c.FILE_NUMBER = $TARGET_FILE_NUMBER;

CREATE TABLE IF NOT EXISTS BACKUP_MFQ_LEGAL_MEMO_112814 AS
SELECT l.*
FROM MFQ_LEGAL_MEMO l
JOIN MFQ_CLAIMS c ON c.CLAIM_ID = l.CLAIM_ID
WHERE c.FILE_NUMBER = $TARGET_FILE_NUMBER;

/* ============================================================================
   3) Base tables behind UI views (documented in 04_create_ui_objects.sql)
   MFQ_CLAIMS_VW            -> MFQ_CLAIMS + MFQ_CLAIM_DEFENDANTS + joins
   MFQ_FORM_WORKSPACE_VW    -> MFQ_CLAIMS_VW + MFQ_SECTIONS + MFQ_QUESTIONS +
                               MFQ_ANSWERS + MFQ_QUESTION_CONFIDENCE
   MFQ_ASSIGNMENT_QUEUE_VW  -> MFQ_ASSIGNMENTS + MFQ_CLAIMS + MFQ_CLAIM_DEFENDANTS
============================================================================ */

/* ============================================================================
   4) Reset data safely (target file only, dependency-aware)
============================================================================ */
DELETE FROM MFQ_QUESTION_CONFIDENCE
WHERE CLAIM_ID IN (SELECT CLAIM_ID FROM MFQ_CLAIMS WHERE FILE_NUMBER = $TARGET_FILE_NUMBER);

DELETE FROM MFQ_ANSWERS
WHERE CLAIM_ID IN (SELECT CLAIM_ID FROM MFQ_CLAIMS WHERE FILE_NUMBER = $TARGET_FILE_NUMBER);

DELETE FROM MFQ_STATUS_HISTORY
WHERE CLAIM_ID IN (SELECT CLAIM_ID FROM MFQ_CLAIMS WHERE FILE_NUMBER = $TARGET_FILE_NUMBER);

DELETE FROM MFQ_ASSIGNMENT_SECTIONS
WHERE CLAIM_ID IN (SELECT CLAIM_ID FROM MFQ_CLAIMS WHERE FILE_NUMBER = $TARGET_FILE_NUMBER);

DELETE FROM MFQ_ASSIGNMENTS
WHERE CLAIM_ID IN (SELECT CLAIM_ID FROM MFQ_CLAIMS WHERE FILE_NUMBER = $TARGET_FILE_NUMBER);

DELETE FROM MFQ_DOCUMENTS
WHERE CLAIM_ID IN (SELECT CLAIM_ID FROM MFQ_CLAIMS WHERE FILE_NUMBER = $TARGET_FILE_NUMBER);

DELETE FROM MFQ_RECORD_SUMMARY
WHERE CLAIM_ID IN (SELECT CLAIM_ID FROM MFQ_CLAIMS WHERE FILE_NUMBER = $TARGET_FILE_NUMBER);

DELETE FROM MFQ_MEDCRON_SUMMARY
WHERE CLAIM_ID IN (SELECT CLAIM_ID FROM MFQ_CLAIMS WHERE FILE_NUMBER = $TARGET_FILE_NUMBER);

DELETE FROM MFQ_LEGAL_MEMO
WHERE CLAIM_ID IN (SELECT CLAIM_ID FROM MFQ_CLAIMS WHERE FILE_NUMBER = $TARGET_FILE_NUMBER);

DELETE FROM MFQ_CLAIM_DEFENDANTS
WHERE CLAIM_ID IN (SELECT CLAIM_ID FROM MFQ_CLAIMS WHERE FILE_NUMBER = $TARGET_FILE_NUMBER);

DELETE FROM MFQ_CLAIMS
WHERE FILE_NUMBER = $TARGET_FILE_NUMBER;

/* ============================================================================
   5) Insert fresh claim/header data
============================================================================ */
SET NEW_CLAIM_ID = UUID_STRING();
SET NEW_DEFENDANT_ID = UUID_STRING();

INSERT INTO MFQ_CLAIMS (
  CLAIM_ID, FILE_NUMBER, PATIENT_NAME, STATUS, PRIORITY, DATE_REQUESTED, CREATED_TS, LAST_UPDATED_TS
)
VALUES (
  $NEW_CLAIM_ID, '112814', $$Ondrea Cummings$$, 'MFQ Generated', 'Medium', CURRENT_DATE(), CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
);

/* ============================================================================
   6) Insert defendant/reviewer data
============================================================================ */
INSERT INTO MFQ_CLAIM_DEFENDANTS (
  DEFENDANT_ID, CLAIM_ID, DEFENDANT_NAME, SPECIALTY, BRIEF_SYNOPSIS, ALLEGED_INJURY_TERMS, ALLEGATION_SUMMARY, CREATED_TS, LAST_UPDATED_TS
)
VALUES (
  $NEW_DEFENDANT_ID,
  $NEW_CLAIM_ID,
  $$Adriana Lopez,MD$$,
  $$OB$$,
  $$Brief Synopsis from completed MFQ PDF for file 112814.$$,
  $$Alleged Injury from completed MFQ PDF for file 112814.$$,
  $$Summary Of Allegations from completed MFQ PDF for file 112814.$$,
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);

/* ============================================================================
   7/8) Insert MFQ answers using PDF field -> QUESTION_KEY -> QUESTION_ID mapping
============================================================================ */
CREATE OR REPLACE TEMP TABLE TMP_MFQ_PDF_FIELDS (
  PDF_FIELD_NAME STRING,
  ANSWER_TEXT STRING
);

INSERT INTO TMP_MFQ_PDF_FIELDS (PDF_FIELD_NAME, ANSWER_TEXT)
SELECT * FROM VALUES
  ('File_No', $$112814$$),
  ('MagMutual_Contact', $$Kira Ptachcinski$$),
  ('MagMutual_Contact_Phone', $$803-731-7577$$),
  ('MagMutual_Contact_Email', $$kptachcinski@magmutual.com$$),
  ('Patient_Name', $$Ondrea Cummings$$),
  ('Defendant_Name', $$Adriana Lopez,MD$$),
  ('Defendant_Specialty', $$OB$$),
  ('Reviewer_Name', $$Adrienne Adams,MD$$),
  ('Reviewer_Specialty', $$OB$$),
  ('Reviewer_PhoneNumber', $$773-909-5425$$),
  ('Reviewer_Email', $$aadams4@nm.org$$),
  ('Brief_Synopsis', $$Brief Synopsis from completed MFQ PDF for file 112814.$$),
  ('Alleged_Injury', $$Alleged Injury from completed MFQ PDF for file 112814.$$),
  ('Summary_Of_Allegations', $$Summary Of Allegations from completed MFQ PDF for file 112814.$$),
  ('Overview_Q1', $$YES$$), ('Overview_Q2', $$PRIMARY_ROLE$$), ('Overview_Q2_Comments', $$Primary treating physician.$$), ('Overview_Q3', $$NO$$),
  ('Patient_Injury', $$Shoulder dystocia with neonatal injury.$$), ('Degree_Of_Injury_Alleged', $$Severe$$), ('Degree_Of_Injury_Suffered', $$Moderate$$), ('Degree_Of_Injury_Alleged_vs_Suffered', $$Partially consistent.$$), ('Injury_Impact', $$Long-term therapy required.$$);

CREATE OR REPLACE TEMP TABLE TMP_MFQ_PDF_TO_QUESTION_KEY (
  PDF_FIELD_NAME STRING,
  QUESTION_KEY STRING
);

INSERT INTO TMP_MFQ_PDF_TO_QUESTION_KEY (PDF_FIELD_NAME, QUESTION_KEY)
SELECT * FROM VALUES
  ('File_No','COVER_MAG_FILE'),('MagMutual_Contact','COVER_CONTACT'),('MagMutual_Contact_Phone','COVER_CONTACT_PHONE'),('MagMutual_Contact_Email','COVER_CONTACT_EMAIL'),
  ('Patient_Name','COVER_PATIENT_NAME'),('Defendant_Name','COVER_DEFENDANT_NAME'),('Defendant_Specialty','COVER_DEFENDANT_SPECIALTY'),('Reviewer_Name','COVER_REVIEWER_NAME'),
  ('Reviewer_Specialty','COVER_REVIEWER_SPECIALTY'),('Reviewer_PhoneNumber','COVER_REVIEWER_PHONE'),('Reviewer_Email','COVER_REVIEWER_EMAIL'),('Brief_Synopsis','COVER_BRIEF_SYNOPSIS'),
  ('Alleged_Injury','COVER_ALLEGED_INJURY'),('Summary_Of_Allegations','COVER_ALLEGATION_SUMMARY'),
  ('Overview_Q1','S1_Q1'),('Overview_Q2','S1_Q2'),('Overview_Q2_Comments','S1_Q2_BRIEF'),('Overview_Q3','S1_Q3'),
  ('Patient_Injury','S2_Q1'),('Degree_Of_Injury_Alleged','S2_Q2_ALLEGED'),('Degree_Of_Injury_Suffered','S2_Q2_SUFFERED'),('Degree_Of_Injury_Alleged_vs_Suffered','S2_Q3'),('Injury_Impact','S2_Q4'),
  ('Intake_Q1a','S3A_Q1'),('Intake_Q2a','S3A_Q2'),('Intake_Q3a','S3A_Q3'),('Intake_Q4a','S3A_Q4'),('Intake_Q4b','S3A_Q4_DEVIATION'),('Intake_Q4c','S3A_Q4_IMPACT'),('Intake_Q5a','S3A_Q5'),('Intake_Q6a','S3A_Q6'),('Intake_Q7a','S3A_Q7'),('Intake_Q8','S3A_Q8'),
  ('DiagnosticWorkUp_Q1a','S3B_Q1'),('DiagnosticWorkUp_Q2a','S3B_Q2'),('DiagnosticWorkUp_Q3a','S3B_Q3'),('DiagnosticWorkUp_Q4a','S3B_Q4'),('DiagnosticWorkUp_Q5a','S3B_Q5'),('DiagnosticWorkUp_Q6a','S3B_Q6'),('DiagnosticWorkUp_Q7a','S3B_Q7'),('DiagnosticWorkUp_Q8a','S3B_Q8'),('DiagnosticWorkUp_Q9a','S3B_Q9'),('DiagnosticWorkUp_Q10','S3B_Q10'),
  ('Treatment_Q1a','S3C_Q1'),('Treatment_Q1a_Explain','S3C_Q1_DETAIL'),('Treatment_Q1b','S3C_Q1_DEVIATION'),('Treatment_Q1b_Explain','S3C_Q1_DEVIATION_EXPLAIN'),('Treatment_Q1c','S3C_Q1_IMPACT'),('Treatment_Q1c_Explain','S3C_Q1_IMPACT_EXPLAIN'),
  ('Treatment_Q2a','S3C_Q2'),('Treatment_Q2a_Explain','S3C_Q2_DETAIL'),('Treatment_Q2b','S3C_Q2_DEVIATION'),('Treatment_Q2b_Explain','S3C_Q2_DEVIATION_EXPLAIN'),('Treatment_Q2c','S3C_Q2_IMPACT'),('Treatment_Q2c_Explain','S3C_Q2_IMPACT_EXPLAIN'),
  ('Treatment_Q3a','S3C_Q3'),('Treatment_Q4a','S3C_Q4'),('Treatment_Q5a','S3C_Q5'),('Treatment_Q6a','S3C_Q6'),('Treatment_Q7a','S3C_Q7'),('Treatment_Q8a','S3C_Q8'),('Treatment_Q9a','S3C_Q9'),('Treatment_Q10','S3C_Q10'),('Treatment_Q10_Explain','S3C_Q10_EXPLAIN'),('Treatment_Q11','S3C_Q11'),
  ('Procedures_Q1','S3D_Q1'),
  ('Monitoring_Q1a','S3E_Q1'),('Monitoring_Q2a','S3E_Q2'),('Monitoring_Q3a','S3E_Q3'),('Monitoring_Q4a','S3E_Q4'),('Monitoring_Q5a','S3E_Q5'),('Monitoring_Q6a','S3E_Q6'),('Monitoring_Q7','S3E_Q7'),('Monitoring_Q8','S3E_Q8'),
  ('Additional_Q1a','S3F_Q1'),('Additional_Q2a','S3F_Q2'),('Additional_Q3a','S3F_Q3'),('Additional_Q4','S3F_Q4'),('Additional_Q5','S3F_Q5'),('Additional_Q6a','S3F_Q6'),('Additional_Q7','S3F_Q7'),('Additional_Q8','S3F_Q8'),
  ('z3_Standard_of_Care_1','S4_Q1'),('Standard_of_Care_1','S4_Q1_COMMENT'),('Check Box1','S4_Q2'),('Standard_Of_Care_Q3','S4_Q3'),
  ('y3_Causation_2','S5_Q1'),('Causation_1a','S5_Q1_COMMENT'),('Check Box2','S5_Q2'),
  ('Closing_Q1','S6_Q1'),('Closing_Q2','S6_Q2'),('Closing_Q3','S6_Q3'),('Closing_Q1_Comments','S6_Q1_COMMENT'),('Closing_Q4_Comments','S6_Q4_COMMENT');

-- Validation: unmapped pdf fields
SELECT f.PDF_FIELD_NAME, f.ANSWER_TEXT
FROM TMP_MFQ_PDF_FIELDS f
LEFT JOIN TMP_MFQ_PDF_TO_QUESTION_KEY m ON m.PDF_FIELD_NAME = f.PDF_FIELD_NAME
WHERE m.QUESTION_KEY IS NULL
ORDER BY f.PDF_FIELD_NAME;

-- Validation: unresolved question_key mappings
SELECT m.PDF_FIELD_NAME, m.QUESTION_KEY
FROM TMP_MFQ_PDF_TO_QUESTION_KEY m
LEFT JOIN MFQ_QUESTIONS q
  ON q.FORM_KEY='MFQ_V1' AND q.IS_CURRENT=TRUE AND q.IS_ACTIVE=TRUE AND q.QUESTION_KEY=m.QUESTION_KEY
WHERE q.QUESTION_ID IS NULL
ORDER BY m.PDF_FIELD_NAME;

CREATE OR REPLACE TEMP TABLE TMP_MFQ_RESOLVED_ANSWERS AS
SELECT f.PDF_FIELD_NAME, m.QUESTION_KEY, q.QUESTION_ID, q.QUESTION_TEXT, f.ANSWER_TEXT
FROM TMP_MFQ_PDF_FIELDS f
JOIN TMP_MFQ_PDF_TO_QUESTION_KEY m ON m.PDF_FIELD_NAME = f.PDF_FIELD_NAME
JOIN MFQ_QUESTIONS q ON q.FORM_KEY='MFQ_V1' AND q.IS_CURRENT=TRUE AND q.IS_ACTIVE=TRUE AND q.QUESTION_KEY=m.QUESTION_KEY
WHERE f.ANSWER_TEXT IS NOT NULL AND TRIM(f.ANSWER_TEXT) <> '';

MERGE INTO MFQ_ANSWERS tgt
USING (
  SELECT UUID_STRING() AS ANSWER_ID, c.CLAIM_ID, c.DEFENDANT_ID, r.QUESTION_ID, r.ANSWER_TEXT, 'EXTRACTED' AS STATUS, TRUE AS IS_CURRENT
  FROM TMP_MFQ_RESOLVED_ANSWERS r
  CROSS JOIN (
    SELECT CLAIM_ID, DEFENDANT_ID
    FROM MFQ_CLAIMS_VW
    WHERE FILE_NUMBER='112814'
    QUALIFY ROW_NUMBER() OVER (ORDER BY CLAIM_ID, DEFENDANT_ID)=1
  ) c
) src
ON tgt.CLAIM_ID=src.CLAIM_ID AND tgt.DEFENDANT_ID=src.DEFENDANT_ID AND tgt.QUESTION_ID=src.QUESTION_ID AND tgt.IS_CURRENT=TRUE
WHEN MATCHED THEN UPDATE SET
  tgt.ANSWER_TEXT=src.ANSWER_TEXT, tgt.STATUS=src.STATUS, tgt.CONFIDENCE_SCORE=1.00, tgt.LAST_UPDATED_TS=CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN INSERT (ANSWER_ID, CLAIM_ID, DEFENDANT_ID, QUESTION_ID, ANSWER_TEXT, ANSWER_JSON, CONFIDENCE_SCORE, STATUS, IS_CURRENT, CREATED_TS, LAST_UPDATED_TS)
VALUES (src.ANSWER_ID, src.CLAIM_ID, src.DEFENDANT_ID, src.QUESTION_ID, src.ANSWER_TEXT, NULL, 1.00, src.STATUS, src.IS_CURRENT, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());

/* ============================================================================
   9) Insert status/history
============================================================================ */
INSERT INTO MFQ_STATUS_HISTORY (
  STATUS_HISTORY_ID, CLAIM_ID, DEFENDANT_ID, EVENT_TYPE, FROM_STATUS, TO_STATUS, EVENT_TS, EVENT_BY_USER_ID, EVENT_NOTE
)
SELECT
  UUID_STRING(), c.CLAIM_ID, d.DEFENDANT_ID, 'PDF_IMPORT', NULL, 'EXTRACTED', CURRENT_TIMESTAMP(), NULL,
  'DEV/TEST import from completed MFQ PDF file 112814'
FROM MFQ_CLAIMS c
JOIN MFQ_CLAIM_DEFENDANTS d ON d.CLAIM_ID = c.CLAIM_ID
WHERE c.FILE_NUMBER = '112814';

/* ============================================================================
   10) Optional confidence data
============================================================================ */
INSERT INTO MFQ_QUESTION_CONFIDENCE (
  QUESTION_CONFIDENCE_ID, CLAIM_ID, DEFENDANT_ID, QUESTION_ID, CONFIDENCE_SCORE, CREATED_TS
)
SELECT
  UUID_STRING(), a.CLAIM_ID, a.DEFENDANT_ID, a.QUESTION_ID, 1.00, CURRENT_TIMESTAMP()
FROM MFQ_ANSWERS a
JOIN MFQ_CLAIMS c ON c.CLAIM_ID = a.CLAIM_ID
WHERE c.FILE_NUMBER = '112814';

/* ============================================================================
   11A) Validate claim exists
============================================================================ */
SELECT *
FROM MFQ_CLAIMS_VW
WHERE FILE_NUMBER = '112814';

/* ============================================================================
   11B) Validate section-wise answer counts
============================================================================ */
SELECT
  SECTION_NAME,
  COUNT(*) AS TOTAL_QUESTIONS,
  COUNT(ANSWER_ID) AS ANSWERED_QUESTIONS,
  COUNT(*) - COUNT(ANSWER_ID) AS MISSING_ANSWERS
FROM MFQ_FORM_WORKSPACE_VW
WHERE CLAIM_ID IN (
  SELECT CLAIM_ID FROM MFQ_CLAIMS_VW WHERE FILE_NUMBER = '112814'
)
AND DEFENDANT_ID IN (
  SELECT DEFENDANT_ID FROM MFQ_CLAIMS_VW WHERE FILE_NUMBER = '112814'
)
GROUP BY SECTION_NAME
ORDER BY SECTION_NAME;

/* ============================================================================
   11C) Validate all answers
============================================================================ */
SELECT
  SECTION_NAME,
  QUESTION_KEY,
  QUESTION_TEXT,
  ANSWER_TEXT,
  ANSWER_STATUS
FROM MFQ_FORM_WORKSPACE_VW
WHERE CLAIM_ID IN (
  SELECT CLAIM_ID FROM MFQ_CLAIMS_VW WHERE FILE_NUMBER = '112814'
)
AND DEFENDANT_ID IN (
  SELECT DEFENDANT_ID FROM MFQ_CLAIMS_VW WHERE FILE_NUMBER = '112814'
)
ORDER BY SECTION_ORDER, QUESTION_ORDER;

/* ============================================================================
   12) Final report queries (run after script)
============================================================================ */
-- Unmapped extracted fields against active MFQ questions.
WITH pdf_answers AS (
  SELECT * FROM VALUES
    ('COVER_MAG_FILE'),('COVER_CONTACT'),('COVER_CONTACT_PHONE'),('COVER_CONTACT_EMAIL'),
    ('COVER_PATIENT_NAME'),('COVER_DEFENDANT_NAME'),('COVER_DEFENDANT_SPECIALTY'),
    ('COVER_REVIEWER_NAME'),('COVER_REVIEWER_SPECIALTY'),('COVER_REVIEWER_PHONE'),
    ('COVER_REVIEWER_EMAIL'),('COVER_BRIEF_SYNOPSIS'),('COVER_ALLEGED_INJURY'),('COVER_ALLEGATION_SUMMARY')
) AS p(QUESTION_KEY)
SELECT p.QUESTION_KEY AS UNMAPPED_FIELD
FROM pdf_answers p
LEFT JOIN MFQ_QUESTIONS q
  ON q.FORM_KEY = 'MFQ_V1'
 AND q.IS_CURRENT = TRUE
 AND q.IS_ACTIVE = TRUE
 AND q.QUESTION_KEY = p.QUESTION_KEY
WHERE q.QUESTION_ID IS NULL
ORDER BY p.QUESTION_KEY;
