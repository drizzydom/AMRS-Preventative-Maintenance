# Sync Auth Staging Checklist (Phase 3)

## Goal
Validate user-scoped sync token auth in staging while preserving backward compatibility for older clients.

## Scope
- Verifies **token issuance**, **token-based sync upload/download**, **legacy fallback**, and **cutover readiness**.
- Assumes no end-user UX changes.

## Prerequisites
- Staging deployed with latest code.
- At least one offline client running latest build.
- At least one legacy/offline client (or test harness) still using legacy sync auth.
- Access to staging server env vars and logs.

## Phase A — Baseline compatibility

### A1. Set server flags
Set these in staging:

```bash
ENABLE_USER_SCOPED_SYNC_TOKEN=true
ALLOW_LEGACY_SYNC_AUTH=true
SYNC_TOKEN_REQUIRE_DEVICE_MATCH=false
SYNC_ACCESS_TOKEN_TTL_SECONDS=43200
```

### A2. Ensure bootstrap remains compatible
Keep bootstrap migration flags in compatibility mode during this phase:

```bash
ALLOW_LEGACY_BOOTSTRAP_TOKEN=true
ENABLE_DEVICE_BOOTSTRAP_TOKEN=true
BOOTSTRAP_REQUIRE_DEVICE_ID=false
BOOTSTRAP_INCLUDE_ADMIN_SYNC_CREDS=true
```

### A3. Verify login succeeds unchanged
- Login from latest client as normal.
- Expected user behavior: no extra prompts/steps.

## Phase B — Token issuance and usage verification

### B1. Verify scoped sync token is issued locally after login
On offline client DB (`app_settings` table), verify keys are populated:

```sql
SELECT key, value
FROM app_settings
WHERE key IN (
  'SYNC_ACCESS_TOKEN',
  'SYNC_ACCESS_TOKEN_USER_ID',
  'SYNC_ACCESS_TOKEN_ISSUED_AT',
  'SYNC_ACCESS_TOKEN_DEVICE_ID'
);
```

**Pass criteria**
- `SYNC_ACCESS_TOKEN` exists and is non-empty.
- `SYNC_ACCESS_TOKEN_USER_ID` matches logged-in user.

### B2. Verify sync upload uses bearer token first
Trigger a local change that enters sync queue (e.g., profile update or maintenance record update), then trigger sync.

Expected log signatures:
- Success path should include a token-auth success message on server side similar to:
  - `"[SYNC AUTH] Bearer token auth successful for user: ..."`
- Client side may log:
  - `"[SYNC] Upload successful with scoped token: 200"`

**Pass criteria**
- Server accepts bearer sync request.
- Data appears on staging server as expected.

### B3. Verify sync download uses bearer token first
Trigger manual/periodic sync download.

Expected behavior:
- Download succeeds with HTTP 200.
- If token is present, bearer path should be attempted first.

**Pass criteria**
- Updated server-side records appear on client after sync.

## Phase C — Fallback behavior verification

### C1. Force bearer failure and verify legacy fallback
Temporarily invalidate local `SYNC_ACCESS_TOKEN` and keep `ALLOW_LEGACY_SYNC_AUTH=true`.

Expected behavior:
- Bearer path fails (401/403).
- Client falls back to legacy session/basic auth and still syncs.

Expected logs:
- Client: `"Scoped token upload failed"` followed by successful fallback upload.
- Server: no bearer success line for that attempt; legacy auth path accepted.

**Pass criteria**
- Sync still completes under fallback.

### C2. Disable fallback and verify strict mode
Set:

```bash
ALLOW_LEGACY_SYNC_AUTH=false
```

Repeat sync test with invalid token.

**Pass criteria**
- Sync fails with unauthorized.
- Restoring valid token returns sync to green.

## Phase D — Device-bound hardening validation

### D1. Enable device-match requirement
Set:

```bash
SYNC_TOKEN_REQUIRE_DEVICE_MATCH=true
```

Test with correct device ID and then wrong/missing device ID.

**Pass criteria**
- Correct device ID: sync succeeds.
- Wrong/missing device ID: sync denied (401/403).

## Phase E — Production readiness gates

Proceed to production rollout only if all are true:
- No end-user UX changes observed.
- Bearer sync path stable for latest clients.
- Legacy fallback validated for old clients.
- Sync data integrity checks pass.
- Monitoring/alerts in place for sync auth failures.

## Suggested rollout order
1. `ENABLE_USER_SCOPED_SYNC_TOKEN=true`
2. Keep `ALLOW_LEGACY_SYNC_AUTH=true` during client rollout
3. Enable `SYNC_TOKEN_REQUIRE_DEVICE_MATCH=true` (after device IDs are stable)
4. Set `ALLOW_LEGACY_SYNC_AUTH=false` when all clients are upgraded

## Fast rollback
If issues occur:

```bash
ENABLE_USER_SCOPED_SYNC_TOKEN=false
ALLOW_LEGACY_SYNC_AUTH=true
SYNC_TOKEN_REQUIRE_DEVICE_MATCH=false
```

Then restart/redeploy service.

---

# Phase 4 — User-Scoped Sync Data Filtering

## Prerequisites
- Phase 3 checklist (phases A-E above) passing.
- At least two test users: one admin, one non-admin with specific site assignments.
- `ENABLE_USER_SCOPED_SYNC_TOKEN=true` and Phase 3 flags already active.

## Phase F — Scoped GET payload validation

### F1. Set Phase 4 flags (compatibility mode)
```bash
ENABLE_USER_SCOPED_SYNC_DATA=true
ALLOW_LEGACY_FULL_SYNC_DATA=true
```

### F2. Admin user sees full dataset
Login as admin user and trigger sync download.

**Pass criteria**
- Server logs: `[SYNC SCOPE] Full-scope sync (admin/legacy)`
- Response `_sync_metadata._sync_scope.mode` == `"full"`
- All sites, machines, parts, records present in payload.

### F3. Non-admin user sees scoped dataset
Login as a non-admin user assigned to **Site A** and **Site B** (but not **Site C**).

**Pass criteria**
- Server logs: `[SYNC SCOPE] Scoped sync for user X: 2 sites, N machines`
- Response `_sync_metadata._sync_scope.mode` == `"scoped"`
- `sites` array contains only Site A and Site B.
- `machines` array contains only machines belonging to Site A / Site B.
- `parts` array contains only parts for those machines.
- `maintenance_records` contains only records for those machines.
- `audit_tasks` contains only tasks for Site A / Site B.
- `users` array contains only users assigned to allowed sites + self.
- `user_sites` contains only associations for allowed sites.
- NO data from Site C appears anywhere in the payload.

### F4. User with no site assignments
Login as a user with no sites assigned. Trigger sync download.

**Pass criteria**
- Server logs: `[SYNC SCOPE] User X has no assigned sites - empty scope`
- Payload `sites`, `machines`, `parts`, `maintenance_records` are all empty arrays.
- `users` array contains at minimum the user's own record.

## Phase G — Scoped POST merge validation

### G1. Valid in-scope POST
From a scoped (non-admin) client assigned to Site A, create a maintenance record for a Site A machine and trigger sync upload.

**Pass criteria**
- Record is accepted and merged on server.
- Response `status` == `"success"`.

### G2. Out-of-scope POST rejection
From the same scoped client, craft a POST body that includes a maintenance record referencing a Site C machine (out of scope).

**Pass criteria**
- Server logs: `[SYNC SCOPE] POST: Dropped 1 out-of-scope 'maintenance_records' records`
- The out-of-scope record does NOT appear in the server database.
- In-scope records in the same POST are still merged successfully.
- Response includes `_sync_scope.records_skipped` > 0.

### G3. User self-update only
From a scoped client, POST a users array with self-update **and** another user's record.

**Pass criteria**
- Self-update is merged.
- Other user's record is dropped (logged as out-of-scope).

## Phase H — Legacy fallback verification

### H1. Legacy client with scoping enabled
Set `ALLOW_LEGACY_FULL_SYNC_DATA=true`. Use a legacy client (basic auth, no bearer token).

**Pass criteria**
- Legacy client receives full dataset (not scoped).
- Server logs: `[SYNC SCOPE] Full-scope sync (admin/legacy)`

### H2. Strict scoping for legacy clients
Set `ALLOW_LEGACY_FULL_SYNC_DATA=false`. Use a legacy client.

**Pass criteria**
- If legacy client has no `g.sync_auth_user_id`, it still gets full data (legacy auth path).
- Verify behavior matches expectations for your deployment scenario.

## Phase I — Production readiness gates (Phase 4)

Proceed to production only if all are true:
- Admin sync payloads unchanged from pre-Phase-4 baseline.
- Non-admin scoped payloads contain ONLY allowed-site data.
- POST scope filtering correctly drops out-of-scope records.
- Dashboard/UI renders correctly with scoped data.
- Legacy clients unaffected (when `ALLOW_LEGACY_FULL_SYNC_DATA=true`).
- No performance degradation on scoped queries.

## Fast rollback (Phase 4)
```bash
ENABLE_USER_SCOPED_SYNC_DATA=false
ALLOW_LEGACY_FULL_SYNC_DATA=true
```
Restart/redeploy service. All clients immediately return to full-sync behavior.

---

## Sanity checks for secrets
After each rollout stage, run:

```bash
git grep -niE "(BOOTSTRAP_TOKEN|BOOTSTRAP_SECRET_TOKEN|SYNC_PASSWORD|AMRS_ADMIN_PASSWORD)[[:space:]_]*[:=][[:space:]]*['\"][^'\"]{8,}['\"]"
```

Expected: no real secrets in tracked files (placeholders only).
