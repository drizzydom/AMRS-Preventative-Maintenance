# Phase 4 Plan: User-Scoped Sync Data Filtering

## Objective
Limit `/api/sync/data` payloads so each client receives only data the authenticated user is allowed to access/manage, while preserving a safe rollback path.

## Non-negotiables
- No additional end-user login/sync steps.
- Backward-compatible rollout with feature flags.
- Quick rollback to full-sync behavior.

## Feature flags
- `ENABLE_USER_SCOPED_SYNC_DATA` (default `false`)
- `ALLOW_LEGACY_FULL_SYNC_DATA` (default `true`)

## Proposed authorization scope model
When bearer token auth is used:
- Resolve `sync_user` from token payload (`user_id`, optional `device_id`).
- Derive accessible site IDs from `user.sites` and role permissions.
- Use role permissions to decide read/write table scope.

When legacy auth is used:
- Keep full behavior unless `ENABLE_USER_SCOPED_SYNC_DATA=true` and `ALLOW_LEGACY_FULL_SYNC_DATA=false`.

## Data filtering rules (initial)

### `users`
- Include only:
  - current user record,
  - plus users needed for referenced ownership/audit metadata if required by UI.
- Exclude unnecessary fields when possible (future hardening).

### `sites`
- Include only sites assigned to the authenticated user (unless admin/full-scope role).

### `machines`
- Include machines whose `site_id` is within allowed sites.

### `parts`
- Include parts where `machine.site_id` is within allowed sites.

### `maintenance_records`
- Include records tied to allowed machines/sites.

### `audit_tasks` / `audit_task_completions` / `machine_audit_task`
- Include records tied to allowed sites/machines only.

### `user_sites`
- Include only associations relevant to current user (or admin scope if enabled).

## Implementation steps
1. Add helper in `app.py`:
   - `_resolve_sync_scope_user()`
   - `_get_allowed_site_ids(sync_user)`
2. Add filtering helpers for each table query path in `sync_data()` GET.
3. Apply scope checks in POST merge path for incoming records:
   - reject/skip records outside scope with audit log.
4. Add metadata in response:
   - `_sync_scope`: `{ mode, user_id, site_count }`
5. Log scope decisions in security/audit logs.

## Testing requirements
- Admin user sees full expected dataset.
- Non-admin user sees only assigned sites and dependent entities.
- Cross-site data does not leak in GET payload.
- POST for out-of-scope records is rejected/skipped.
- Legacy clients continue to function while `ALLOW_LEGACY_FULL_SYNC_DATA=true`.

## Rollout sequence
1. Deploy code with flags defaulted to legacy behavior.
2. Enable `ENABLE_USER_SCOPED_SYNC_DATA=true` in staging.
3. Keep `ALLOW_LEGACY_FULL_SYNC_DATA=true` initially.
4. Validate dashboards/reports for scoped users.
5. Set `ALLOW_LEGACY_FULL_SYNC_DATA=false` in staging.
6. Promote to production in waves.

## Rollback
If any issue occurs:
- `ENABLE_USER_SCOPED_SYNC_DATA=false`
- `ALLOW_LEGACY_FULL_SYNC_DATA=true`

Restart/redeploy service and resume legacy full-sync behavior.
