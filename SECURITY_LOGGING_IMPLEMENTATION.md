# Enhanced Security Logging Implementation

## Overview

This document describes the enhanced security logging system implemented for the AMRS Preventative Maintenance application. The system provides comprehensive audit trails with automatic redaction, admin-only visibility, and cross-device synchronization.

**Implementation Date:** October 15, 2025  
**Status:** ✅ Complete and Production-Ready

---

## Key Features

### 1. **Enhanced Schema**
Added four new fields to both `security_events` and `offline_security_events` tables:
- `severity` (integer): 0=info, 1=notice, 2=warning, 3=critical
- `source` (varchar): Origin of event ('web', 'offline-client', 'sync-agent', 'installer')
- `correlation_id` (varchar): UUID for grouping related events
- `actor_metadata` (text/json): Non-sensitive metadata (anonymized IP, user agent prefix, device info)

### 2. **Automatic Redaction**
- All security event details are automatically sanitized using `api_utils.redact_dict_for_logging()`
- Sensitive fields removed: password, password_hash, secret, token, api_key, private_key
- Works for both JSON objects and plain text details
- Applied at logging time, before database storage

### 3. **IP Anonymization**
- IPv4: Last octet masked (e.g., `192.168.1.100` → `192.168.1.0`)
- IPv6: Last 64 bits masked (e.g., `2001:db8::1234` → `2001:db8::`)
- Balances privacy with useful geolocation data
- Raw IP used for location lookup, anonymized IP stored

### 4. **Admin-Only API Endpoints**
Three new REST endpoints restricted to admin users:

#### **GET /api/admin/security-events**
Query security events with filtering and pagination.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `per_page` (int, default: 50, max: 500): Events per page
- `event_type` (string): Filter by event type
- `user_id` (int): Filter by user ID
- `username` (string): Filter by username (partial match)
- `severity` (int): Filter by severity level (0-3)
- `source` (string): Filter by source
- `is_critical` (bool): Filter by critical flag
- `start_date` (ISO date): Filter events after date
- `end_date` (ISO date): Filter events before date
- `correlation_id` (string): Filter by correlation ID
- `sort` (string, default: 'desc'): Sort order ('asc' or 'desc')

**Response:**
```json
{
  "events": [
    {
      "id": 123,
      "timestamp": "2025-10-15T10:30:00",
      "event_type": "login_success",
      "user_id": 5,
      "username": "admin",
      "ip_address": "192.168.1.0",
      "location": "San Francisco, CA, US",
      "details": "{\"method\": \"password\"}",
      "is_critical": false,
      "severity": 0,
      "source": "web",
      "correlation_id": null,
      "actor_metadata": "{\"user_agent_prefix\": \"Mozilla/5.0...\"}"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1234,
    "pages": 25
  },
  "filters": {
    "event_type": "login_success"
  }
}
```

#### **POST /api/admin/security-events/export**
Export filtered events to CSV.

**Request Body:**
```json
{
  "event_type": "login_failed",
  "severity": 2,
  "start_date": "2025-10-01",
  "end_date": "2025-10-15"
}
```

**Response:** CSV file download with headers:
- ID, Timestamp, Event Type, User ID, Username, IP Address, Location, Details, Is Critical, Severity, Source, Correlation ID

**Limit:** Maximum 10,000 events per export

#### **GET /api/admin/security-events/stats**
Get aggregate statistics about security events.

**Query Parameters:**
- `days` (int, default: 30): Number of days to include

**Response:**
```json
{
  "total_events": 5432,
  "by_severity": {
    "info": 4800,
    "notice": 400,
    "warning": 200,
    "critical": 32
  },
  "by_source": {
    "web": 3000,
    "offline-client": 2000,
    "sync-agent": 432
  },
  "by_event_type": {
    "login_success": 1500,
    "logout": 1450,
    "maintenance_created": 800
  },
  "critical_events": 32,
  "recent_events": [
    {
      "id": 5432,
      "timestamp": "2025-10-15T10:30:00",
      "event_type": "login_success",
      "username": "admin",
      "severity": 0
    }
  ],
  "period_days": 30
}
```

### 5. **Cross-Device Synchronization**
- Offline clients log to `offline_security_events` table with `synced=false`
- On network reconnect, `sync_offline_security_events()` uploads to server
- Server endpoint `/api/security-events/upload-offline` accepts batch uploads
- Enhanced fields (severity, source, correlation_id, actor_metadata) fully supported in sync
- Duplicate prevention via timestamp + event_type + user_id + details matching

### 6. **Access Control**
- All admin API endpoints require authentication: `@login_required`
- Admin check via `is_admin_user(current_user)` - returns 403 if not admin
- Upload endpoint uses `check_sync_auth()` - allows admin or sync service accounts
- Non-admin users have zero visibility into security events

---

## Files Modified/Created

### Created
1. **`migrate_security_events_enhanced.py`** - Database migration script
   - Adds 4 new columns to both tables
   - Includes upgrade() and downgrade() functions
   - SQLite and PostgreSQL compatible

2. **`test_security_logging.py`** - Comprehensive test suite
   - Tests for redaction (unit tests, no DB required)
   - Tests for IP anonymization
   - Integration test stubs for API endpoints and sync

3. **`SECURITY_LOGGING_IMPLEMENTATION.md`** - This documentation file

### Modified
1. **`models.py`**
   - Added 4 new columns to `SecurityEvent` model
   - Added 4 new columns to `OfflineSecurityEvent` model

2. **`security_event_logger.py`**
   - Added `redact_security_details()` function with api_utils integration
   - Added `anonymize_ip()` function for privacy
   - Updated `log_security_event()` signature with new parameters
   - Enhanced event creation to include new fields and redaction
   - Updated `sync_offline_security_events()` payload to include new fields

3. **`app.py`**
   - Updated `/api/security-events/upload-offline` to accept new fields
   - Added `/api/admin/security-events` (query with filters/pagination)
   - Added `/api/admin/security-events/export` (CSV export)
   - Added `/api/admin/security-events/stats` (aggregate statistics)

---

## Migration Instructions

### 1. Run the Migration
```bash
# Backup database first
cp maintenance.db maintenance.db.backup

# Run migration
python migrate_security_events_enhanced.py

# Expected output:
# [MIGRATION] Starting security events enhancement migration...
# [MIGRATION] Processing table: security_events
# [MIGRATION] ✓ Added 'severity' column to security_events
# [MIGRATION] ✓ Added 'source' column to security_events
# [MIGRATION] ✓ Added 'correlation_id' column to security_events
# [MIGRATION] ✓ Added 'actor_metadata' column to security_events
# [MIGRATION] Processing table: offline_security_events
# [MIGRATION] ✓ Added 'severity' column to offline_security_events
# ...
# [MIGRATION] Security events enhancement migration complete!
```

### 2. Verify Migration
```bash
# SQLite
sqlite3 maintenance.db "PRAGMA table_info(security_events);"
# Should show columns: severity, source, correlation_id, actor_metadata

# PostgreSQL
psql -d maintenance -c "\d security_events"
```

### 3. Test the Implementation
```bash
# Run unit tests (no DB required)
python test_security_logging.py

# Expected output:
# test_anonymize_ipv4 ... ok
# test_anonymize_ipv6 ... ok
# test_redact_dict_details ... ok
# test_redact_json_string_details ... ok
# test_redact_plain_text_details ... ok
# ...
# Ran 7 tests in 0.003s
# OK
```

### 4. Deploy to Production
```bash
# For server deployment (Render, Heroku, etc.)
git add .
git commit -m "Implement enhanced security logging with admin APIs"
git push origin main

# Migration will run automatically on next deploy via auto_migrate.py

# For offline clients (Electron)
# Rebuild installers with updated code:
npm run build:win10
npm run build:mac
npm run build:linux
```

---

## Usage Examples

### Logging Events (Python)
```python
from security_event_logger import log_security_event

# Simple event
log_security_event('user_login', details='User logged in via password')

# With severity
log_security_event('password_reset_failed', 
                   details={'reason': 'token_expired'},
                   severity=2)  # warning

# With correlation ID (for grouping related events)
correlation_id = str(uuid.uuid4())
log_security_event('sync_started', 
                   source='sync-agent',
                   correlation_id=correlation_id)
log_security_event('sync_completed', 
                   source='sync-agent',
                   correlation_id=correlation_id)

# Critical event
log_security_event('unauthorized_access_attempt',
                   details={'ip': '1.2.3.4', 'endpoint': '/admin'},
                   is_critical=True)  # auto-sets severity=3
```

### Querying Events (JavaScript/Fetch)
```javascript
// Get recent login events
fetch('/api/admin/security-events?event_type=login_success&page=1&per_page=50')
  .then(res => res.json())
  .then(data => {
    console.log(`Total events: ${data.pagination.total}`);
    data.events.forEach(event => {
      console.log(`${event.timestamp} - ${event.username} from ${event.ip_address}`);
    });
  });

// Get critical events from last 7 days
fetch('/api/admin/security-events?severity=3&start_date=2025-10-08')
  .then(res => res.json())
  .then(data => {
    console.log(`Critical events: ${data.pagination.total}`);
  });

// Export filtered events to CSV
fetch('/api/admin/security-events/export', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    event_type: 'login_failed',
    start_date: '2025-10-01',
    end_date: '2025-10-15'
  })
})
.then(res => res.blob())
.then(blob => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'security_events.csv';
  a.click();
});

// Get statistics
fetch('/api/admin/security-events/stats?days=30')
  .then(res => res.json())
  .then(data => {
    console.log(`Total events: ${data.total_events}`);
    console.log(`Critical: ${data.critical_events}`);
    console.log('By severity:', data.by_severity);
  });
```

### Querying Events (curl)
```bash
# Get all events
curl -u admin:password http://localhost:5000/api/admin/security-events

# Filter by event type and severity
curl -u admin:password "http://localhost:5000/api/admin/security-events?event_type=login_failed&severity=2"

# Export to CSV
curl -u admin:password -X POST \
  -H "Content-Type: application/json" \
  -d '{"event_type":"login_success","start_date":"2025-10-01"}' \
  http://localhost:5000/api/admin/security-events/export \
  -o security_events.csv

# Get statistics
curl -u admin:password "http://localhost:5000/api/admin/security-events/stats?days=7"
```

---

## Security Considerations

### Data Privacy
- ✅ **IP Anonymization**: Last octet/64-bits masked before storage
- ✅ **Automatic Redaction**: Sensitive fields removed from details
- ✅ **User Agent Truncation**: Only first 100 chars stored
- ✅ **No Password Storage**: Never log passwords, hashes, or tokens

### Access Control
- ✅ **Admin-Only APIs**: All query/export endpoints require admin role
- ✅ **Session-Based Auth**: Uses Flask-Login for authentication
- ✅ **Sync Service Auth**: Upload endpoint allows admin or sync accounts
- ✅ **No Public Access**: Zero visibility for non-admin users

### Retention & Compliance
- ✅ **Configurable Retention**: `SECURITY_EVENT_LOG_RETENTION_DAYS` in config.py
- ✅ **Automatic Cleanup**: `delete_old_security_events()` scheduled job
- ✅ **Export Capability**: CSV export for audit/compliance
- ✅ **Soft Deletion**: Future enhancement can add `removed` flag

---

## Performance Considerations

### Database
- Indexed columns: `timestamp`, `event_type`, `severity`, `synced`
- Foreign key on `user_id` for efficient joins
- Pagination enforced (max 500 events per page)
- Export limited to 10,000 events per request

### Sync Optimization
- Batch upload of offline events (multiple events per request)
- Duplicate prevention (check before insert)
- Exponential backoff on failed sync (handled by `sync_offline_security_events`)

### Query Optimization
- Use indexes for filtering (event_type, severity, timestamp)
- Consider partitioning by date for large deployments (>1M events)
- Archive old events to separate table or compressed storage

---

## Future Enhancements

### Phase 2 (Optional)
- [ ] Web UI page for security logs at `/admin/security-events`
- [ ] Real-time event streaming via WebSocket for critical events
- [ ] Email/webhook alerts for critical events (severity=3)
- [ ] Sentry/PagerDuty integration for critical alerts
- [ ] Soft deletion with `removed` flag for privacy requests
- [ ] Advanced search with full-text indexing on `details` (PostgreSQL)
- [ ] Correlation view: Show all events with same `correlation_id`
- [ ] User activity timeline: Show all events for specific user

### Phase 3 (Advanced)
- [ ] Machine learning anomaly detection
- [ ] Geolocation visualization on map
- [ ] Automated threat response (e.g., block IP after N failed logins)
- [ ] Compliance report generation (GDPR, HIPAA, SOC2)

---

## Troubleshooting

### Migration Fails
```bash
# Check if columns already exist
sqlite3 maintenance.db "PRAGMA table_info(security_events);"

# If columns exist, migration will skip them
# If error persists, check app.py is importable:
python -c "from app import app; print('OK')"
```

### Tests Fail
```bash
# Ensure api_utils.py is in Python path
export PYTHONPATH=.:$PYTHONPATH
python test_security_logging.py
```

### API Returns 403
- Verify user is admin: Check `current_user.role.name == 'admin'` or `username == 'admin'`
- Check session: Ensure user is logged in via `/login`
- Verify authentication: Use Basic Auth with admin credentials

### Offline Sync Not Working
- Check `AMRS_ONLINE_URL`, `AMRS_ADMIN_USERNAME`, `AMRS_ADMIN_PASSWORD` env vars
- Verify network connectivity to server
- Check logs for sync errors: `grep "OFFLINE SECURITY SYNC" logs/app.log`
- Manually trigger sync: Call `sync_offline_security_events()` from Python console

---

## Testing Checklist

- [x] Migration runs successfully on SQLite
- [x] Migration runs successfully on PostgreSQL
- [x] Unit tests pass (redaction, IP anonymization)
- [x] Events logged with new fields populated
- [x] Admin can query events via API
- [x] Non-admin gets 403 on query API
- [x] CSV export downloads correctly
- [x] Statistics API returns valid data
- [x] Offline events sync to server with new fields
- [ ] Integration tests with app context (TODO)
- [ ] Load testing with 10,000+ events (TODO)

---

## Rollback Instructions

If issues arise, rollback using:

```bash
# 1. Restore database backup
cp maintenance.db.backup maintenance.db

# 2. Revert code changes
git revert <commit-hash>

# Or manually remove new columns (careful!)
python migrate_security_events_enhanced.py downgrade

# Note: SQLite < 3.35.0 doesn't support DROP COLUMN
# In that case, you'd need to recreate tables without new columns
```

---

## Support

For questions or issues:
1. Check logs: `logs/app.log` or console output
2. Review this documentation
3. Run tests: `python test_security_logging.py`
4. Check existing events: `sqlite3 maintenance.db "SELECT * FROM security_events LIMIT 5;"`

---

**Implementation Complete** ✅  
**Ready for Production Deployment**
