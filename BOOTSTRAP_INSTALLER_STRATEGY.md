# AMRS Preventative Maintenance: Complete Bootstrap, Sync & Offline Mode Strategy

## Project Status & Context
This document contains all context for picking up the AMRS Preventative Maintenance project's bootstrap, keyring secrets, and offline synchronization features on a new device.

### Current Implementation Status (as of chat session)
- ✅ **Flask endpoint fixes completed** - BuildError and template issues resolved
- ✅ **Performance optimizations implemented** - Eliminated excessive sync queue growth (was 5000+ entries)
- ✅ **Offline mode configured** - True SQLite offline mode with PostgreSQL online mode
- ✅ **Bootstrap process restructured** - Keyring-based secret management with remote server download
- ✅ **Python environment fixed** - Using 3.11.9 venv for SQLAlchemy compatibility (Python 3.13 had issues)
- ✅ **Security logging parameter fixes** - Corrected log_security_event function calls in bootstrap endpoint
- 🔄 **Bootstrap endpoint functionality** - Recently fixed TypeError issues, needs testing
- ❌ **User login in offline mode** - Blocked by bootstrap process (fresh SQLite DB has no user credentials)

## Core Architecture Overview

### Database Modes
- **Online Mode**: PostgreSQL database on Render (production server)
- **Offline Mode**: SQLite database (`maintenance.db`) for desktop/Electron clients
- **Mode Detection**: Via `is_offline_mode()` in `timezone_utils.py` - checks if `DATABASE_URL` starts with `sqlite://` or is empty

### Bootstrap & Secret Management System
The application uses a sophisticated keyring-based secret management system:

1. **Environment Variables Loading** (`.env` file)
2. **Keyring Secret Bootstrap** (`bootstrap_secrets_from_remote()`)
3. **Remote Secret Download** (from online server via `/api/bootstrap-secrets`)
4. **Local Keyring Storage** (OS-level secure storage)

### Performance Optimization Features
- **Sync Cooldown**: 60-second minimum between sync attempts (`_sync_cooldown_seconds`)
- **Offline Mode Detection**: Prevents sync operations on online server or when using PostgreSQL
- **Delayed Sync Batching**: Groups sync operations to reduce server load
- **Enhanced Sync Queue**: Optimized queue management with status tracking

## Implementation Details

### 1. Bootstrap Secrets Function (`app.py` lines 189-287)
```python
def bootstrap_secrets_from_remote():
    """Bootstrap secrets from remote server and store in keyring if missing."""
    KEYRING_SERVICE = "amrs"
    KEYRING_KEYS = [
        "USER_FIELD_ENCRYPTION_KEY", "RENDER_EXTERNAL_URL", "SYNC_URL",
        "SYNC_USERNAME", "AMRS_ONLINE_URL", "AMRS_ADMIN_USERNAME", 
        "AMRS_ADMIN_PASSWORD", "MAIL_SERVER", "MAIL_PORT", "MAIL_USE_TLS",
        "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_DEFAULT_SENDER", 
        "SECRET_KEY", "BOOTSTRAP_SECRET_TOKEN"
    ]
```

### 2. Bootstrap API Endpoint (`app.py` lines 670-695)
```python
@app.route('/api/bootstrap-secrets', methods=['POST'])
def bootstrap_secrets():
    """Return essential sync secrets for desktop bootstrap, protected by a bootstrap token."""
    # Bearer token authentication
    # Security event logging with correct parameters: log_security_event(event_type, details, is_critical)
    # Returns JSON with all required secrets for offline operation
```

### 3. Environment Configuration (`.env`)
```properties
# Key settings for offline testing:
USER_FIELD_ENCRYPTION_KEY=_CY9_bO9vrX2CEUNmFqD1ETx-CluNejbidXFGMYapis=
# DATABASE_URL=postgresql://... (COMMENTED OUT to force SQLite offline mode)
BOOTSTRAP_URL=https://amrs-pm-test.onrender.com/api/bootstrap-secrets
BOOTSTRAP_SECRET_TOKEN=d735X9BQNwd1YZUU_DtFs7WeRsvn0WTttSrPE_jdyVxtxa8IFw0vQBlmaRv_1pLO
AMRS_ONLINE_URL=https://amrs-pm-test.onrender.com
AMRS_ADMIN_USERNAME=dmoriello
AMRS_ADMIN_PASSWORD=Sm@rty123
```

### 4. Performance Optimization Functions (`sync_utils_enhanced.py`)
```python
def should_trigger_sync():
    """Determine if sync should be triggered based on environment and timing."""
    # Checks: is_online_server(), is_offline_mode(), cooldown period
    # Only allows sync for true offline SQLite clients

def add_to_sync_queue_enhanced(table_name, record_id, operation, payload_dict, immediate_sync=True, force_add=False):
    """Enhanced sync queue with performance optimizations."""
    # Skips sync queue on online server unless forced
    # Uses timezone-aware datetime handling
```

### 5. Timezone & Mode Detection (`timezone_utils.py`)
```python
def is_online_server():
    """Check if this is the online server (Render, Heroku, etc.)"""
    # Checks for RENDER, HEROKU, RAILWAY env vars or IS_ONLINE_SERVER='true'

def is_offline_mode():
    """Check if running in true offline mode (SQLite database)."""
    # Checks if DATABASE_URL starts with 'sqlite://' or is empty
```

## Recent Bug Fixes Applied

### Security Logging Parameter Fix
**Issue**: Bootstrap endpoint was failing with `TypeError: log_security_event() got an unexpected keyword argument 'user_id'`

**Solution**: Fixed function calls in bootstrap endpoint to use correct parameters:
```python
# WRONG (was causing 500 errors):
log_security_event(user_id=None, username=None, context=event_context, message="...")

# CORRECT (fixed):
log_security_event(event_type="bootstrap_secrets_denied", details="Denied bootstrap secrets from {remote_addr}: invalid or missing token", is_critical=True)
```

### Import Order Fix
**Issue**: Keyring secret loading was happening before .env file loading, causing bootstrap failures.

**Solution**: Restructured `app.py` to load `.env` first (lines 180-188), then attempt keyring bootstrap (lines 287).

## Current Blockers & Next Steps

### Primary Blocker: User Authentication in Offline Mode
**Problem**: Fresh SQLite database has no user credentials, preventing login to test sync functionality.

**Root Cause**: Bootstrap process downloads secrets but doesn't populate initial user data.

**Required Solution**: 
1. Test bootstrap endpoint functionality after recent TypeError fixes
2. Implement initial data sync after successful bootstrap to populate user credentials
3. Ensure offline SQLite database has at least one admin user for testing

### Testing Procedure for Bootstrap
1. **Clear existing keyring secrets**: Delete all AMRS-related entries from OS keyring
2. **Start application**: Should trigger `bootstrap_secrets_from_remote()`
3. **Verify secret download**: Check logs for successful bootstrap from `https://amrs-pm-test.onrender.com/api/bootstrap-secrets`
4. **Confirm keyring storage**: Verify secrets are stored in OS keyring under service "amrs"
5. **Test initial sync**: Ensure sync_db.py or equivalent runs to populate initial user data

## Build/Packaging Strategy for Electron

### 1. Secure Token Injection (Build Time)
- Use PyInstaller or Electron packager to inject `BOOTSTRAP_SECRET_TOKEN` at build time
- Store token as encrypted resource or environment variable in packaged app
- Never commit token to source control

### 2. First-Run Bootstrap Script
```python
def first_run_bootstrap():
    """Run on first app launch to set up keyring and download secrets."""
    # Extract BOOTSTRAP_SECRET_TOKEN from packaged resource
    # Store in keyring: keyring.set_password('amrs', 'BOOTSTRAP_SECRET_TOKEN', token)
    # Trigger bootstrap_secrets_from_remote()
    # Run initial data sync to populate SQLite with user credentials
    # Create default admin user if none exists
```

### 3. App Startup Logic
```python
def app_startup():
    """Main app startup with bootstrap handling."""
    # 1. Load .env file
    # 2. Attempt bootstrap_secrets_from_remote()
    # 3. If successful, trigger initial data sync
    # 4. Ensure default admin user exists
    # 5. Start enhanced sync worker for ongoing sync
```

## File Modifications Made

### `app.py`
- **Lines 180-188**: Added .env loading before keyring operations
- **Lines 189-287**: Created `bootstrap_secrets_from_remote()` function
- **Lines 670-695**: Fixed bootstrap endpoint with correct `log_security_event` parameters
- **Bootstrap success tracking**: Added global `bootstrap_success` variable for triggering initial sync

### `timezone_utils.py`
- **Lines 75-87**: Added `is_offline_mode()` function for SQLite detection
- **Lines 63-73**: Enhanced `is_online_server()` for better platform detection

### `sync_utils_enhanced.py`
- **Lines 24-45**: Added `should_trigger_sync()` with cooldown and mode detection
- **Lines 47-85**: Enhanced `add_to_sync_queue_enhanced()` with performance optimizations
- **Performance settings**: `_sync_cooldown_seconds = 60` for preventing excessive sync

### `.env`
- **Commented out DATABASE_URL**: Forces SQLite offline mode for testing
- **Added BOOTSTRAP_URL and BOOTSTRAP_SECRET_TOKEN**: For remote secret download

## Debugging Commands & Tools

### Test Bootstrap Endpoint
```powershell
# PowerShell command to test bootstrap endpoint:
$headers = @{ "Authorization" = "Bearer d735X9BQNwd1YZUU_DtFs7WeRsvn0WTttSrPE_jdyVxtxa8IFw0vQBlmaRv_1pLO" }
Invoke-RestMethod -Uri "https://amrs-pm-test.onrender.com/api/bootstrap-secrets" -Method POST -Headers $headers
```

### Check Keyring Contents
```python
import keyring
service = "amrs"
keys = ["USER_FIELD_ENCRYPTION_KEY", "BOOTSTRAP_SECRET_TOKEN", "AMRS_ADMIN_USERNAME"]
for key in keys:
    value = keyring.get_password(service, key)
    print(f"{key}: {'SET' if value else 'NOT SET'}")
```

### Manual Sync Database
```bash
python sync_db.py --url "https://amrs-pm-test.onrender.com" --username "dmoriello" --password "Sm@rty123"
```

## Security Considerations

### Token Rotation
- `BOOTSTRAP_SECRET_TOKEN` should be rotated periodically
- Monitor bootstrap endpoint access logs for unauthorized attempts
- Consider implementing rate limiting on bootstrap endpoint

### Keyring Security
- OS keyring provides secure storage for desktop applications
- Secrets are encrypted and tied to user account
- Cross-platform compatibility (Windows Credential Manager, macOS Keychain, Linux Secret Service)

### Network Security
- Bootstrap endpoint uses HTTPS with Bearer token authentication
- All sync operations use HTTP Basic Auth with admin credentials
- Security event logging tracks all bootstrap attempts

## Recovery Procedures

### If Bootstrap Fails
1. **Check network connectivity** to `https://amrs-pm-test.onrender.com`
2. **Verify BOOTSTRAP_SECRET_TOKEN** in `.env` file
3. **Clear keyring secrets** and retry bootstrap
4. **Check server logs** for bootstrap endpoint errors
5. **Fallback**: Manually set environment variables in `.env`

### If Sync Fails
1. **Verify AMRS_ADMIN_USERNAME/AMRS_ADMIN_PASSWORD** are correct
2. **Check sync_queue table** for pending entries
3. **Run manual sync**: Use `sync_db.py` script
4. **Clear sync queue**: Reset pending entries if corrupted

### If Login Fails in Offline Mode
1. **Check SQLite database**: Ensure users table has entries
2. **Run initial data sync**: Download user data from online server
3. **Create emergency admin**: Use `add_default_admin_if_needed()` function
4. **Reset user passwords**: Use password reset functionality

---

## Quick Start for New Machine

1. **Clone repository**: `git clone <repo-url> && cd AMRS-Preventative-Maintenance`
2. **Setup Python 3.11.9 venv**: `python -m venv .venv && .venv\Scripts\activate`
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Copy this file to Copilot Chat**: Share context for implementation help
5. **Run application**: `python app.py` (will auto-bootstrap if configured)
6. **Test bootstrap**: Check logs for successful secret download
7. **Verify login**: Ensure offline SQLite mode allows user authentication

**Critical Files to Focus On:**
- `app.py` (lines 180-287, 670-695) - Bootstrap logic
- `timezone_utils.py` (lines 63-87) - Mode detection
- `sync_utils_enhanced.py` (lines 24-85) - Performance optimization
- `.env` - Environment configuration
- `security_event_logger.py` - Correct function signatures

**Ask Copilot Chat**: "Help me test and fix the bootstrap endpoint functionality to enable user login in offline SQLite mode after downloading secrets from the online server."
