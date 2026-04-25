# MagMutual MFQ Enterprise Portal Discovery Analysis

_Date: 2026-04-25_

## 1) Current repository structure (as-is)

- Root repo currently contains a single implementation directory `A27EXCIDK7BA295Y/` and minimal top-level docs (`README.md`).
- Current app is a Streamlit in Snowflake prototype with these top-level modules:
  - `streamlit_app.py` (entrypoint / page router)
  - `pages/` (dashboard, claims, claim details, reports)
  - `components/` (cards, filters, tables, layout, forms, badges)
  - `services/` (Snowflake session + CRUD/query helper functions)
  - `utils/` (constants, session-state helpers)
  - `styles/` (single custom CSS file)
- Uploaded artifacts are present in `A27EXCIDK7BA295Y/`:
  - `MFQ_UI_Portal_Requirements_and_Screen_Design.docx`
  - `MagM - UI Portal Prototype.zip` (contains `.pptx`)
  - `tables and SQL's for questionarire.zip`
  - `MASTER_COPY_Medical_Faculty_Questionnaire (1).pdf`

## 2) Requirements document findings (`.docx`)

Core goals extracted from the requirements document:
- Human-in-the-loop claim review.
- Role-based access by persona: Claims Analyst, Advice Team, Medical Faculty, Executives, Admin.
- AI confidence-driven review routing and section-level collaboration.
- Key modules expected:
  - Dashboard
  - Claims / work queue
  - Claim details header + tabbed workspace
  - MFQ Form
  - Records Summary
  - MedCron
  - Legal Memo
  - Enquiries + AI Assist
  - Documents
  - Reports & Analytics
  - Admin & RBAC
  - Notifications
  - Appian workflow trigger integration
- Explicit screen catalog S1-S11 and design notes call out:
  - Role-scoped visibility and actions
  - Section-level assignment and edit restrictions
  - Confidence guidance (never auto-approval)
  - Export/report capabilities
  - Audit and governance expectations

## 3) UI prototype findings (`.pptx` from ZIP)

Prototype slides reinforce the requirements and add interaction details:
- Persona-switched login concept exists in prototype.
- Dashboard, notifications, claim list, claim details tabs, and regenerate flow are shown.
- Claim detail includes MFQ review workspace and assignment flow where one or more sections can be assigned to selected medical faculty.
- Medical Faculty persona constraints are explicitly called out:
  - Can approve/reject MFQ review request.
  - Should not access Legal Memo / MedChron (as stated in prototype notes).
  - Should not access reports.
  - Should have restricted download access for certain artifacts.
- Separate slides exist for reports (analyst/admin summary contexts).

## 4) SQL/table script findings (`tables and SQL's for questionarire.zip`)

### 4.1 SQL package contents
- `00_session_context.sql`: environment/session variables and source-object bindings.
- `01_create_core_objects.sql`: core data model creation.
- `02_create_views.sql`: source and operational views.
- `03_seed_system_config.sql`: pipeline/model/routing/workflow/summary configuration seeds.
- `05_seed_questionnaire.sql`: MFQ v1 section/question metadata seed.

### 4.2 Core schema objects observed
- Configuration/metadata:
  - `PIPELINE_CONFIG`, `LLM_CONFIG`, `LLM_ROUTING`, `WORKFLOW_STATUS_DEF`, `PROMPT_TEMPLATE`, `PROMPT_TEMPLATE_HISTORY`, `SUMMARY_CONFIG`
- Questionnaire model:
  - `QST_SECTION`, `QST_QUESTION`
- Claim domain:
  - `CLAIM`, `CLAIM_DEFENDANT`
- Pipeline execution/audit:
  - `PIPELINE_RUN`, `CLAIM_COMPONENT_STATUS`, `PIPELINE_AUDIT_EVENT`, `AGENT_STEP_LOG`, `REGENERATION_LOG`
- AI output and review artifacts:
  - `DOCUMENT_SENTENCE_EMBEDDINGS`, `CHRONOLOGY_EVENT`, `GAP_HYPOTHESIS`, `GAP_FINDING`, `MFQ_ANSWER`, `LLM_EVALUATION`, `CLAIM_SUMMARY`, `HUMAN_REVIEW`
- Views:
  - `VW_OCR_CLAIM_SOURCE`, `VW_OCR_CLAIM_SENTENCES`, `VW_CURRENT_ANSWERS`, `VW_PENDING_REVIEWS`

### 4.3 Seed content observations
- `LLM_ROUTING` seeds multiple task types (embedding, chronology, gap analysis, answer generation, summary).
- `SUMMARY_CONFIG` defines summary modes (medical care, injury, chronology narrative, allegation analysis, SOC, causation, full claim).
- `QST_SECTION` seeds 12 sections for `MFQ_V1`, including:
  - `SEC_COVER`, `SEC_I`, `SEC_II`, `SEC_III_A`..`SEC_III_F`, `SEC_IV`, `SEC_V`, `SEC_VI`
- `QST_QUESTION` seed script appears extensive (336 question insert statements in current file).

## 5) Current implementation gap summary

The existing Streamlit prototype already covers a subset of requirements:
- Present: dashboard, claims list, claim detail tabs, MFQ section rendering, reports, basic role switch UX.
- Missing/partial relative to enterprise target:
  - Formal admin/RBAC management screens and permission policies.
  - Notification center workflow integration.
  - Appian trigger integration.
  - Fine-grained section assignment UX and state model.
  - Robust workflow status engine and audit timeline UI.
  - Production-grade service layer boundaries, error handling, telemetry, and test coverage.
  - Clear separation between data access, domain logic, and UI composition.

## 6) Proposed enterprise target architecture

### 6.1 Proposed folder structure

```text
mfq_enterprise_portal/
  app.py
  config/
    settings.py
    roles.py
    feature_flags.py
  ui/
    pages/
      dashboard.py
      claims_queue.py
      claim_detail.py
      mfq_workspace.py
      records_summary.py
      medcron.py
      legal_memo.py
      enquiries_ai_assist.py
      documents.py
      reports_analytics.py
      admin_rbac.py
      notifications.py
    components/
      navigation.py
      kpi_cards.py
      claims_table.py
      filters.py
      status_badges.py
      confidence_widgets.py
      assignment_panel.py
      approval_actions.py
      document_viewer.py
      charts.py
      toasts.py
      modals.py
      audit_timeline.py
    styles/
      theme.css
  domain/
    models/
      claim.py
      questionnaire.py
      review.py
      workflow.py
      user_role.py
    policies/
      rbac_policy.py
      visibility_policy.py
      assignment_policy.py
      transition_policy.py
    use_cases/
      get_dashboard_metrics.py
      search_claims.py
      load_claim_workspace.py
      assign_sections.py
      submit_review_decision.py
      regenerate_mfq.py
      generate_reports.py
  services/
    snowflake/
      session.py
      repositories/
        claim_repository.py
        questionnaire_repository.py
        review_repository.py
        report_repository.py
        admin_repository.py
      sql/
        claims.sql
        dashboard.sql
        reports.sql
        admin.sql
    integration/
      appian_client.py
      notifications_client.py
      ai_assist_service.py
    observability/
      logging.py
      metrics.py
      tracing.py
  data/
    sql/
      000_session_context.sql
      010_core_tables.sql
      020_views.sql
      030_seed_config.sql
      040_seed_questionnaire.sql
      050_rbac_tables.sql
      060_app_views_for_streamlit.sql
      070_row_access_policies.sql
      080_masking_policies.sql
  tests/
    unit/
    integration/
    sql/
  docs/
    architecture.md
    rbac_matrix.md
    workflow_states.md
    deployment.md
```

### 6.2 Required SQL scripts (recommended set)

1. Environment bootstrap: role, warehouse, database/schema, stage.
2. Core domain tables: claims, defendants, pipeline runs, questionnaire, answers, evaluation, summary, review, regeneration.
3. App-facing views for Streamlit pages (dashboard queue, claim header, section answers, reports aggregates, pending reviews).
4. RBAC tables and mapping:
   - users, groups, roles, persona mappings
   - claim assignment (claim + section level)
5. Workflow state/transition metadata and validation procedures.
6. Audit/event logging tables + standardized insert procedures.
7. Row access policies and masking policies for PHI-sensitive fields.
8. Seed scripts for questionnaire and status definitions.
9. Optional task/stream/procedure scripts for batch regeneration and Appian trigger handoff.

### 6.3 Required Streamlit pages

- Dashboard (role-tailored KPIs and workload)
- Claims queue (tabs/filters/search/sort)
- Claim detail shell (header + tab routing)
- MFQ Workspace (section review/edit/confidence)
- Records Summary
- MedCron
- Legal Memo
- Enquiries / AI Assist
- Documents (download restrictions by role)
- Reports & Analytics
- Admin & RBAC
- Notifications center
- (Optional) Audit Explorer for admin/compliance

### 6.4 Required reusable components

- App shell / navbar / sidebar / breadcrumbs
- Persona badge + permission-aware action bar
- KPI cards
- Claims table with status/priority/confidence chips
- Filter bar (status, priority, assignee, date, confidence)
- Section accordion + question cards
- Confidence panel (overall + section-level)
- Assignment drawer/modal (single/multi-section)
- Approve/reject dialog with reason capture
- Report chart components
- Document list/download guard component
- Notification bell + panel
- Audit timeline component
- Standard empty/error/loading components

### 6.5 Required services

- Authentication/session context service (Snowflake user + role).
- RBAC authorization service (page + action + data scope checks).
- Claim query service (search/filter/pagination).
- MFQ form service (load/save answers, lock/edit policies).
- Assignment service (claim/section assignment and reassignment).
- Workflow orchestration service (state transitions and validations).
- Regeneration service (new document detection + rerun trigger).
- Reporting service (aggregates + exports).
- Notifications service.
- AI Assist service with strict context/RBAC filtering.
- Appian integration service (outbound triggers + status callbacks).
- Audit/telemetry service.

### 6.6 Missing assumptions / decisions needed

1. System of record for identity (Snowflake native users vs SSO/SCIM source).
2. Exact persona-to-Snowflake role mapping and entitlement matrix.
3. Final policy for Medical Faculty access to MedCron/Legal Memo (requirements vs prototype “say” note must be confirmed).
4. Definition of “claim ownership” and queue tab semantics (New/In Review/Returned/Processed).
5. Source of truth for assignment (claim-only vs section-only vs hybrid).
6. Required response-time SLAs and expected record volumes.
7. Data-retention/audit requirements (regulatory and legal hold).
8. Export controls: who can download which artifacts and in what format.
9. Appian integration contract (payloads, retry, idempotency, and error handling).
10. AI model governance: approved Cortex models, fallback, cost controls, and review thresholds.
11. Definition of done for “enterprise-ready” (security review, test coverage, observability baseline).

### 6.7 Step-by-step development plan

1. **Discovery & alignment**
   - Finalize requirement ambiguities and RBAC matrix.
   - Confirm non-functional requirements (performance, availability, security).
2. **Foundation setup**
   - Establish repo layout, coding standards, environment configs.
   - Define domain models and service interfaces.
3. **Data platform implementation**
   - Build/validate core tables, views, policies, and seeds in Snowflake.
   - Add migration/versioning approach for SQL changes.
4. **Core backend/service layer**
   - Implement repositories and use cases (dashboard, claims, detail, answers, assignments).
   - Add workflow transition guards and audit logging.
5. **MVP UI delivery**
   - Build Dashboard, Claims Queue, Claim Detail shell, MFQ Workspace.
   - Add role-aware navigation and action controls.
6. **Evidence & collaboration modules**
   - Implement Records Summary, MedCron, Legal Memo, Enquiries/AI Assist, Documents.
   - Enforce persona-specific visibility and download constraints.
7. **Operational modules**
   - Build Reports & Analytics and Notifications center.
   - Add exports and scheduled report generation hooks.
8. **Admin & governance**
   - Build Admin/RBAC screens and assignment rules management.
   - Add comprehensive audit explorer and error monitoring dashboards.
9. **Integration hardening**
   - Integrate Appian triggers and callback/state reconciliation.
   - Add retry/idempotency safeguards.
10. **Quality & release**
   - Unit/integration/UAT, security review, performance validation.
   - Production rollout plan, runbooks, and post-launch monitoring.
