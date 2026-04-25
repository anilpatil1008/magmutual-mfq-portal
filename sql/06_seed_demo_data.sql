-- 06_seed_demo_data.sql
-- Demo seed for enterprise prototype walkthrough.

INSERT INTO MFQ_APP_USERS (USERNAME, APP_ROLE, IS_ACTIVE)
SELECT 'ANALYST_1', 'Claims Analyst', TRUE UNION ALL
SELECT 'ADVICE_1', 'Advice Team', TRUE UNION ALL
SELECT 'FACULTY_1', 'Medical Faculty', TRUE UNION ALL
SELECT 'EXEC_1', 'Executive', TRUE UNION ALL
SELECT 'ADMIN_1', 'Admin', TRUE;

INSERT INTO MFQ_ROLE_PAGE_ACCESS (APP_ROLE, PAGE_KEY, IS_ALLOWED)
SELECT 'Claims Analyst', 'Dashboard', TRUE UNION ALL
SELECT 'Claims Analyst', 'Claims', TRUE UNION ALL
SELECT 'Claims Analyst', 'Claim Details', TRUE UNION ALL
SELECT 'Claims Analyst', 'Reports', TRUE UNION ALL
SELECT 'Advice Team', 'Dashboard', TRUE UNION ALL
SELECT 'Advice Team', 'Claims', TRUE UNION ALL
SELECT 'Medical Faculty', 'Dashboard', TRUE UNION ALL
SELECT 'Medical Faculty', 'Claims', TRUE UNION ALL
SELECT 'Medical Faculty', 'Claim Details', TRUE UNION ALL
SELECT 'Executive', 'Dashboard', TRUE UNION ALL
SELECT 'Executive', 'Reports', TRUE UNION ALL
SELECT 'Admin', 'Admin', TRUE;

INSERT INTO MFQ_ASSIGNMENT_RULES (RULE_ID, SPECIALTY, DEFAULT_FACULTY, IS_ACTIVE)
SELECT 'R-OB-1', 'OB/GYN', 'FACULTY_1', TRUE UNION ALL
SELECT 'R-ER-1', 'Emergency Medicine', 'FACULTY_2', TRUE UNION ALL
SELECT 'R-IM-1', 'Internal Medicine', 'FACULTY_3', TRUE;

INSERT INTO MFQ_NOTIFICATIONS (NOTIFICATION_ID, TARGET_USER, TITLE, MESSAGE, SEVERITY, IS_READ)
SELECT UUID_STRING(), 'ALL', 'Daily Queue Refresh', 'Claim queue has been refreshed from workflow pipeline.', 'info', FALSE UNION ALL
SELECT UUID_STRING(), 'ANALYST_1', 'Missing Document Alert', 'Claim C-10014 requires additional operative notes.', 'warning', FALSE UNION ALL
SELECT UUID_STRING(), 'FACULTY_1', 'Assignment Received', 'New section assignment waiting for review.', 'success', FALSE UNION ALL
SELECT UUID_STRING(), 'ADMIN_1', 'RBAC Change Audit', 'Two page-access mappings changed in the last 24 hours.', 'info', FALSE;
