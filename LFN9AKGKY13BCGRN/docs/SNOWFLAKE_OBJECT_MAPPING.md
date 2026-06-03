# Snowflake Object Mapping

## Central Registry
All object names should be maintained in `config/snowflake_objects.py`.

## Current Mapping
- Dashboard summary -> `MFQ_DASHBOARD_SUMMARY_VW` via `MFQ_DASHBOARD_SUMMARY_VIEW` in `config/snowflake_objects.py`.
- Claims list/search -> `VW_MFQ_CLAIMS` via `MFQ_CLAIMS_LIST_VIEW` in `config/snowflake_objects.py`.
- Admin Users tab -> `APP_USER`, `APP_USER_ROLE`, `APP_ROLE` via `repositories.admin_repository.get_users_with_roles`.
- Admin Role Mappings tab -> `APP_ROLE_PERMISSION`, `APP_ROLE`, `APP_PERMISSION` via `repositories.admin_repository.get_role_permissions`.
- Admin Permissions tab -> `MFQ_ASSIGNMENT_QUEUE_VW` via `repositories.admin_repository.get_assignment_queue`.
- Header Notifications -> `MFQ_NOTIFICATIONS_VW` / `MFQ_NOTIFICATIONS` via `repositories.notifications_repository`.
- Claims workflows -> multiple `MFQ_*` objects (currently mostly in `services/claim_service.py`; progressively migrating).

## How to Rename an Object
1. Update the constant in `config/snowflake_objects.py`.
2. Verify impacted repository methods compile/query correctly.
3. Run app smoke tests and object validator.
4. Avoid page-level SQL changes unless introducing a new repository method.
