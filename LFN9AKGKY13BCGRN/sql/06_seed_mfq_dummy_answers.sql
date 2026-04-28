USE ROLE ACCOUNTADMIN;
USE WAREHOUSE COMPUTE_WH;
USE DATABASE MAGMUTUAL_MFQ_APP;
USE SCHEMA PUBLIC;

-- Demo claim for MFQ auto-population.
SET CLAIM_ID = 'CLM-1002';
SET DEFENDANT_ID = (
  SELECT DEFENDANT_ID
  FROM MFQ_CLAIM_DEFENDANTS
  WHERE CLAIM_ID = $CLAIM_ID
  ORDER BY DEFENDANT_ID
  LIMIT 1
);

-- Insert missing text answers only (do not overwrite current answers).
INSERT INTO MFQ_ANSWERS
(
  ANSWER_ID,
  CLAIM_ID,
  DEFENDANT_ID,
  QUESTION_ID,
  ANSWER_TEXT,
  ANSWER_JSON,
  CONFIDENCE_SCORE,
  STATUS,
  IS_CURRENT,
  CREATED_TS,
  LAST_UPDATED_TS
)
SELECT
  UUID_STRING(),
  $CLAIM_ID,
  $DEFENDANT_ID,
  q.QUESTION_ID,
  CASE
    WHEN q.QUESTION_TEXT ILIKE '%explain%' THEN
      'Based on the available medical records, this response summarizes the relevant chronology and clinical rationale for the allegation.'
    WHEN q.QUESTION_TEXT ILIKE '%deviation%' THEN
      'No clear deviation from accepted practice is evident in the currently available records.'
    WHEN q.QUESTION_TEXT ILIKE '%impact%' THEN
      'The records reviewed do not show a clearly attributable impact on patient outcome at this stage.'
    ELSE
      CONCAT('Generated MFQ narrative response for ', q.QUESTION_KEY, ' based on currently available claim documentation.')
  END AS ANSWER_TEXT,
  PARSE_JSON(
    OBJECT_CONSTRUCT(
      'value',
      CASE
        WHEN q.QUESTION_TEXT ILIKE '%explain%' THEN
          'Based on the available medical records, this response summarizes the relevant chronology and clinical rationale for the allegation.'
        WHEN q.QUESTION_TEXT ILIKE '%deviation%' THEN
          'No clear deviation from accepted practice is evident in the currently available records.'
        WHEN q.QUESTION_TEXT ILIKE '%impact%' THEN
          'The records reviewed do not show a clearly attributable impact on patient outcome at this stage.'
        ELSE
          CONCAT('Generated MFQ narrative response for ', q.QUESTION_KEY, ' based on currently available claim documentation.')
      END
    )
  ),
  92,
  'AI_GENERATED',
  TRUE,
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
FROM MFQ_QUESTIONS q
WHERE q.FORM_KEY = 'MFQ_V1'
  AND q.IS_ACTIVE = TRUE
  AND q.IS_CURRENT = TRUE
  AND q.ANSWER_TYPE = 'TEXT'
  AND NOT EXISTS (
    SELECT 1
    FROM MFQ_ANSWERS a
    WHERE a.CLAIM_ID = $CLAIM_ID
      AND a.QUESTION_ID = q.QUESTION_ID
      AND a.IS_CURRENT = TRUE
  );

-- Insert missing yes/no/choice/rating/select answers only.
INSERT INTO MFQ_ANSWERS
(
  ANSWER_ID,
  CLAIM_ID,
  DEFENDANT_ID,
  QUESTION_ID,
  ANSWER_TEXT,
  ANSWER_JSON,
  CONFIDENCE_SCORE,
  STATUS,
  IS_CURRENT,
  CREATED_TS,
  LAST_UPDATED_TS
)
SELECT
  UUID_STRING(),
  $CLAIM_ID,
  $DEFENDANT_ID,
  q.QUESTION_ID,
  CASE
    WHEN q.ANSWER_TYPE IN ('YES_NO', 'YES_NO_UNCLEAR', 'YES_NO_UNCLEAR_NA', 'CHOICE') THEN
      CASE
        WHEN q.QUESTION_TEXT ILIKE '%deviation%' THEN 'NO'
        WHEN q.QUESTION_TEXT ILIKE '%impact%' THEN 'NO'
        ELSE COALESCE(q.ALLOWED_VALUES[0]::STRING, 'YES')
      END
    WHEN q.ANSWER_TYPE IN ('RATING_1_9', 'RATING_1_5', 'SELECT') THEN COALESCE(q.ALLOWED_VALUES[0]::STRING, '1')
    ELSE NULL
  END AS ANSWER_TEXT,
  PARSE_JSON(
    OBJECT_CONSTRUCT(
      'value',
      CASE
        WHEN q.ANSWER_TYPE IN ('YES_NO', 'YES_NO_UNCLEAR', 'YES_NO_UNCLEAR_NA', 'CHOICE') THEN
          CASE
            WHEN q.QUESTION_TEXT ILIKE '%deviation%' THEN 'NO'
            WHEN q.QUESTION_TEXT ILIKE '%impact%' THEN 'NO'
            ELSE COALESCE(q.ALLOWED_VALUES[0]::STRING, 'YES')
          END
        WHEN q.ANSWER_TYPE IN ('RATING_1_9', 'RATING_1_5', 'SELECT') THEN COALESCE(q.ALLOWED_VALUES[0]::STRING, '1')
        ELSE NULL
      END
    )
  ),
  90,
  'AI_GENERATED',
  TRUE,
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
FROM MFQ_QUESTIONS q
WHERE q.FORM_KEY = 'MFQ_V1'
  AND q.IS_ACTIVE = TRUE
  AND q.IS_CURRENT = TRUE
  AND q.ANSWER_TYPE IN ('YES_NO', 'YES_NO_UNCLEAR', 'YES_NO_UNCLEAR_NA', 'CHOICE', 'RATING_1_9', 'RATING_1_5', 'SELECT')
  AND NOT EXISTS (
    SELECT 1
    FROM MFQ_ANSWERS a
    WHERE a.CLAIM_ID = $CLAIM_ID
      AND a.QUESTION_ID = q.QUESTION_ID
      AND a.IS_CURRENT = TRUE
  );

-- Insert missing multiselect answers only.
INSERT INTO MFQ_ANSWERS
(
  ANSWER_ID,
  CLAIM_ID,
  DEFENDANT_ID,
  QUESTION_ID,
  ANSWER_TEXT,
  ANSWER_JSON,
  CONFIDENCE_SCORE,
  STATUS,
  IS_CURRENT,
  CREATED_TS,
  LAST_UPDATED_TS
)
SELECT
  UUID_STRING(),
  $CLAIM_ID,
  $DEFENDANT_ID,
  q.QUESTION_ID,
  NULL,
  PARSE_JSON(
    OBJECT_CONSTRUCT(
      'value',
      IFF(ARRAY_SIZE(q.ALLOWED_VALUES) > 0, ARRAY_CONSTRUCT(q.ALLOWED_VALUES[0]::STRING), ARRAY_CONSTRUCT())
    )
  ),
  89,
  'AI_GENERATED',
  TRUE,
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
FROM MFQ_QUESTIONS q
WHERE q.FORM_KEY = 'MFQ_V1'
  AND q.IS_ACTIVE = TRUE
  AND q.IS_CURRENT = TRUE
  AND q.ANSWER_TYPE = 'MULTISELECT'
  AND NOT EXISTS (
    SELECT 1
    FROM MFQ_ANSWERS a
    WHERE a.CLAIM_ID = $CLAIM_ID
      AND a.QUESTION_ID = q.QUESTION_ID
      AND a.IS_CURRENT = TRUE
  );

-- Validation query: ensure all active questions have answer rows for CLM-1002.
SELECT
  s.SECTION_NAME,
  q.QUESTION_KEY,
  q.QUESTION_TEXT,
  q.ANSWER_TYPE,
  a.ANSWER_TEXT,
  a.ANSWER_JSON,
  a.CONFIDENCE_SCORE
FROM MFQ_SECTIONS s
JOIN MFQ_QUESTIONS q
  ON q.SECTION_ID = s.SECTION_ID
LEFT JOIN MFQ_ANSWERS a
  ON a.QUESTION_ID = q.QUESTION_ID
 AND a.CLAIM_ID = $CLAIM_ID
 AND a.IS_CURRENT = TRUE
WHERE s.FORM_KEY = 'MFQ_V1'
ORDER BY s.DISPLAY_ORDER, q.DISPLAY_ORDER;

SELECT COUNT(*) AS TOTAL_QUESTIONS
FROM MFQ_QUESTIONS
WHERE FORM_KEY = 'MFQ_V1'
  AND IS_ACTIVE = TRUE
  AND IS_CURRENT = TRUE;

SELECT COUNT(*) AS TOTAL_ANSWERS
FROM MFQ_ANSWERS
WHERE CLAIM_ID = $CLAIM_ID
  AND IS_CURRENT = TRUE;
