# Security Logging Audit & Implementation Plan

## Executive Summary

This document provides a comprehensive audit of existing security logging and a strategic plan for adding missing logging points. The goal is to ensure comprehensive security coverage while **avoiding database bloat** through appropriate severity level assignment.

---

## Current Security Logging Coverage

### ✅ Already Logging (18 calls in app.py)

#### Authentication Events
1. **Login Success** (line 6989) - Severity: 0 (info)
2. **Login Failed** (line 7024) - Severity: 1 (notice)
3. **Login New Device/IP** (line 6994) - Severity: 0 (info) - _Consider removing to reduce bloat_
4. **Logout** (line 7037) - Severity: 0 (info)

#### Password Management
5. **Password Reset Request** - Via forgot_password endpoint
6. **Password Reset Failed - Short Password** (line 7140) - Severity: 1 (notice)
7. **Password Reset Failed - Mismatch** (line 7147) - Severity: 1 (notice)
8. **Password Reset Success** (line 7159) - Severity: 1 (notice)

#### Bootstrap Secrets (Offline Client Setup)
9. **Bootstrap Secrets Denied** (line 2724) - Severity: 3 (critical)
10. **Bootstrap Secrets Success** (line 2731) - Severity: 1 (notice)

#### User Management (Admin Actions)
11. **Admin User Change** (line 5866) - Severity: 2 (warning) - All user CRUD

#### Authorization Violations
12. **Privilege Escalation Attempt** (line 7993) - Severity: 3 (critical) - Non-admin creating site
13. **Suspicious Activity - Unauthorized Site Access** (line 8145) - Severity: 3 (critical)
14. **Suspicious Activity - Unauthorized Machine Access** (line 8345) - Severity: 3 (critical)

---

## 🚨 Critical Missing Logging Points

### High-Priority Additions (Severity 2-3)

#### 1. Admin Access Denials
**Problem:** Admin routes redirect without logging who tried to access them.
**Impact:** No audit trail of unauthorized admin access attempts.
**Locations:**
- `/admin` (line 4608)
- `/admin/security-logs` (line 4585)
- `/admin/toggle-security-logging` (line 4677)
- `/admin/audit-history` (line 4694)
- `/admin/excel-import` (line 4719)
- `/admin/users` (line 5860)
- `/admin/roles` (line 6085)
- `/admin/<section>` (line 7969)
- All admin API endpoints (lines 1014, 1130, 1242)

**Recommended Severity:** 2 (warning) - These are legitimate users trying to access admin features without permission.

**Implementation:**
```python
if not is_admin_user(current_user):
    log_security_event(
        event_type="admin_access_denied",
        details=f"User {current_user.username} attempted to access admin route: {request.path}",
        severity=2,
        source='web'
    )
    flash('You do not have permission to access this page.', 'danger')
    return redirect(url_for('dashboard'))
```

#### 2. Site Access Violations (Additional Locations)
**Problem:** Multiple locations check site access but don't all log violations.
**Locations:**
- `/admin/<section>` machines filtering (line 8209)
- Parts management site filtering (line 8603)
- Parts access validation (line 8627)
- Task filtering by site (line 8672)

**Recommended Severity:** 2 (warning) - User attempting to access data outside their permissions.

#### 3. User Management Actions (Currently Too Broad)
**Problem:** Line 5866 logs ALL user changes with request.form (overly verbose, contains passwords).
**Recommendation:** Split into specific events with better redaction:
- `user_created` (severity: 1)
- `user_updated` (severity: 1)
- `user_deleted` (severity: 2)
- `user_role_changed` (severity: 2)

#### 4. Role & Permission Changes
**Problem:** No logging when roles are created, modified, or deleted.
**Locations:**
- `/admin/roles` POST (line 6080+)
- Role updates/deletes (lines 6283, 6316)

**Recommended Severity:** 2 (warning) - Permission changes are security-relevant.

#### 5. Data Export Operations
**Problem:** No logging when users export sensitive data (CSV, reports).
**Impact:** No audit trail of data extraction.
**Recommended Severity:** 1 (notice) for regular users, 0 (info) for routine exports.

#### 6. Configuration Changes
**Problem:** Only security logging toggle is tracked (line 4674).
**Missing:** Other app settings changes, database schema changes.
**Recommended Severity:** 1 (notice)

---

## 🔍 Medium-Priority Additions (Severity 0-1)

### 7. Offline Sync Events
**Current:** Security events are synced, but sync failures aren't logged.
**Add:**
- `sync_started` (severity: 0)
- `sync_completed` (severity: 0)
- `sync_failed` (severity: 1) - Network/auth errors
- `sync_conflict_detected` (severity: 1)

**Location:** `sync_db.py` or similar sync handlers.

### 8. Bulk Data Operations
**Problem:** Excel import, bulk machine creation not logged.
**Locations:**
- `/admin/excel-import` processing
- Bulk maintenance record creation

**Recommended Severity:** 1 (notice) - Notable operations but not critical.

### 9. First-Time Events
**Add:**
- First login by user (severity: 0)
- First successful sync after offline period (severity: 0)
- Application version upgrade detected (severity: 0)

---

## ⚠️ Logging to Remove or Downgrade (Bloat Prevention)

### 1. Login New Device/IP (line 6994)
**Problem:** Logs on EVERY login, not just actual new devices.
**Current Severity:** Not specified (defaults to 0)
**Recommendation:** **REMOVE** - This creates unnecessary bloat. If needed, implement proper device fingerprinting and only log when actually new.

### 2. Overly Verbose Details
**Problem:** Line 5866 logs entire `request.form` including passwords.
**Recommendation:** Use `redact_security_details()` more aggressively, or log only specific fields.

---

## 📊 Severity Assignment Guidelines

To prevent database bloat, follow these rules:

### Severity 0 (Info) - Use Sparingly
- Routine successful operations (login, logout)
- First-time events (first login, version upgrade)
- **Should be <30% of total events**

### Severity 1 (Notice) - Default for Normal Operations
- Password resets (successful)
- User/role creation
- Data exports
- Configuration changes
- Sync completions
- **Should be ~50% of total events**

### Severity 2 (Warning) - Suspicious Activity
- Authorization failures (non-admin accessing admin routes)
- Repeated login failures (rate limiting trigger)
- Site/machine access violations
- Role/permission changes
- **Should be ~15% of total events**

### Severity 3 (Critical) - Security Incidents
- Bootstrap secrets denied (potential compromise)
- Privilege escalation attempts
- Successful unauthorized data access (should never happen)
- Multiple failed authentications from same IP (brute force)
- **Should be <5% of total events**

---

## 🎯 Implementation Strategy

### Phase 1: Critical Fixes (Week 1)
1. **Add logging to ALL admin access denial points** (severity: 2)
2. **Split user management logging** into specific events with redaction
3. **Remove "login_new_device_or_ip"** to prevent bloat
4. **Add role/permission change logging** (severity: 2)

### Phase 2: Medium Priority (Week 2)
5. **Add sync event logging** (sync_failed severity: 1)
6. **Add data export logging** (severity: 1)
7. **Add configuration change logging** (severity: 1)

### Phase 3: Nice-to-Have (Week 3+)
8. **Bulk operation logging** (Excel import, etc.)
9. **First-time event tracking**
10. **Rate limiting / brute force detection** (multiple failures → severity: 3)

---

## 📝 Code Templates

### Template 1: Admin Access Denial
```python
if not is_admin_user(current_user):
    from security_event_logger import log_security_event
    log_security_event(
        event_type="admin_access_denied",
        details=f"Attempted access to: {request.path}",
        severity=2,
        source='web'
    )
    flash('You do not have permission to access this page.', 'danger')
    return redirect(url_for('dashboard'))
```

### Template 2: Split User Management Events
```python
# Replace line 5866's single log with:
if creating_user:
    log_security_event(
        event_type="user_created",
        details=f"Created user: {username}, role: {role.name if role else 'None'}",
        severity=1,
        source='web'
    )
elif updating_user:
    log_security_event(
        event_type="user_updated",
        details=f"Updated user_id: {user_id}, fields: {', '.join(updated_fields)}",
        severity=1,
        source='web'
    )
```

### Template 3: Data Export Logging
```python
log_security_event(
    event_type="data_export",
    details=f"Exported {export_type}: {record_count} records, format: {format}",
    severity=1,
    source='web'
)
```

### Template 4: Sync Failure Logging (offline client)
```python
# In sync_db.py or similar
except Exception as e:
    log_security_event(
        event_type="sync_failed",
        details=f"Sync failure: {str(e)[:200]}",  # Truncate long errors
        severity=1,
        source='offline-client'
    )
```

---

## 🔒 Security Considerations

1. **Always use automatic redaction** - `redact_security_details()` removes passwords, tokens, keys
2. **Always anonymize IPs** - `anonymize_ip()` masks last octet/64-bits
3. **Truncate long details** - Limit to 500 chars to prevent bloat
4. **Use correlation_id for multi-step operations** - Group related events (e.g., password reset flow)
5. **Set appropriate source** - 'web', 'offline-client', 'sync-agent', 'installer'

---

## 📈 Expected Impact

### Before Implementation
- **Events/Day:** ~200-500 (mostly login/logout)
- **Severity Distribution:** 
  - 0 (info): 60% (lots of "new device" noise)
  - 1 (notice): 30%
  - 2 (warning): 8%
  - 3 (critical): 2%

### After Implementation (Phase 1 + 2)
- **Events/Day:** ~300-600 (slight increase, but more meaningful)
- **Severity Distribution:**
  - 0 (info): 25% (reduced by removing "new device" logs)
  - 1 (notice): 55% (password resets, data exports, sync, config)
  - 2 (warning): 18% (admin denials, site violations, role changes)
  - 3 (critical): 2% (bootstrap failures, privilege escalation)

### Database Growth
- **Current:** ~5 MB/month (estimated)
- **After Phase 1+2:** ~6-7 MB/month (20-40% increase)
- **With 90-day retention:** ~20 MB total

---

## ✅ Testing Checklist

After implementation:
1. [ ] Test admin access denial logging (try accessing `/admin` as non-admin)
2. [ ] Test user CRUD logging (create, update, delete user)
3. [ ] Test role change logging
4. [ ] Test site access violation logging
5. [ ] Test sync failure logging (disconnect network during sync)
6. [ ] Test data export logging
7. [ ] Verify automatic redaction works (password in details → "[REDACTED]")
8. [ ] Verify IP anonymization (x.x.x.255 → x.x.x.0)
9. [ ] Verify offline sync uploads all new events
10. [ ] Check severity distribution in admin panel after 1 week

---

## 🎓 Best Practices Summary

**DO:**
- Use severity 0 for routine, high-frequency events
- Use severity 1 for normal security-relevant operations (default)
- Use severity 2 for suspicious/unauthorized access attempts
- Use severity 3 only for actual security incidents
- Always redact sensitive details before logging
- Truncate long error messages to prevent bloat
- Use correlation_id for multi-step flows

**DON'T:**
- Log every single user action (creates bloat)
- Log full request.form (contains passwords)
- Log raw IP addresses (use anonymized)
- Use severity 3 for normal operations
- Log same event multiple times in a flow
- Forget to set appropriate `source` parameter

---

## Next Steps

1. **Review this document** - Approve severity assignments and priorities
2. **Implement Phase 1** - Critical admin access logging
3. **Deploy to test environment** - Validate logging doesn't create performance issues
4. **Monitor for 1 week** - Check severity distribution and database growth
5. **Adjust if needed** - Tune severity levels or remove noisy logs
6. **Implement Phase 2** - Medium-priority additions
7. **Document for team** - Update security logging guidelines

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-15  
**Author:** Security Logging Audit System
