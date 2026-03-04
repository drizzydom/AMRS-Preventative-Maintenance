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

## Sanity checks for secrets
After each rollout stage, run:

```bash
git grep -niE "(BOOTSTRAP_TOKEN|BOOTSTRAP_SECRET_TOKEN|SYNC_PASSWORD|AMRS_ADMIN_PASSWORD)[[:space:]_]*[:=][[:space:]]*['\"][^'\"]{8,}['\"]"
```

Expected: no real secrets in tracked files (placeholders only).
