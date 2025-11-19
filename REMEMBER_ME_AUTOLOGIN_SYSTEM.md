# Remember Me / Auto-Login System Implementation

## Current Device-Bound Architecture (November 2025)

The remember-me system now stores one hashed token per device in the new `remember_sessions` table. Each session record tracks the device identifier, fingerprint, user agent, IP fragment, and rotation metadata so we can bind long-lived cookies to specific hardware without ever storing the raw token server-side.

### Highlights

- **90-day rolling TTL** driven by `REMEMBER_TOKEN_DAYS` (default 90) with automatic rotation on every successful validation.
- **Device-bound cookies**: `remember_session_id` (numeric id), `remember_token` (rotating secret), and `remember_device_id` (client-supplied identifier persisted via localStorage). All cookies support SameSite + Secure/HttpOnly policies configured in Flask.
- **Session caps** enforced by `REMEMBER_MAX_SESSIONS` (default 5). Oldest sessions are revoked automatically after the limit is exceeded.
- **Fingerprint enforcement** using a hash of device id + user agent + truncated IP. Mismatches instantly revoke the session.
- **Legacy compatibility**: existing single `remember_token` cookies are upgraded into a managed `RememberSession` the next time they are presented, so older clients can transition seamlessly.

### Database Schema (Current)

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `users` | `remember_token`, `remember_token_expiration`, `remember_enabled` | Legacy single-token fallback so older offline clients continue working. Automatically cleared once sessions migrate. |
| `remember_sessions` | `id`, `user_id`, `token_hash`, `device_id`, `device_fingerprint`, `issued_at`, `last_used_at`, `expires_at`, `revoked_at` | Stores one hashed token per device along with auditing metadata. `token_hash` is SHA-256 of the browser secret; `device_id` is a sanitized 64-char identifier sourced from the React/Electron client. |

Table creation is handled by SQLAlchemy's `db.create_all()`/auto-migration flow, so deployments automatically pick up the new schema as long as migrations run during startup.

### Request Lifecycle

1. **Login (`/api/v1/auth/login`)**
  - Clients send `username`, `password`, `remember_me`, and a stable `device_id` (persisted locally). All API requests also include `X-Device-Id` headers so the server can correlate follow-up traffic.
  - When `remember_me` is checked, `remember_session_manager.create_or_update_session()` creates/rotates a record, enforces per-user limits, and queues cookies via `queue_cookie_refresh()`.
  - Unchecked logins revoke existing sessions for that device and queue cookie clearing instructions.
2. **Auto-login (`before_request` in `app.py`)**
  - Reads the trio of cookies plus the fingerprint derived from headers and IP.
  - Calls `validate_session()` which verifies hashes, fingerprint, device id, and expiration before rotating the token and extending TTL.
  - If validation fails, the session is revoked and cookies are cleared; the legacy cookie (if present) is also invalidated.
3. **Logout (`/logout` + `/api/v1/auth/logout`)**
  - Loads the device id from cookies, revokes matching sessions, logs the action, and queues cookie clearing payloads.

### Configuration & Client Requirements

- `REMEMBER_TOKEN_DAYS` (default **90**) controls token TTL; `REMEMBER_MAX_SESSIONS` (default **5**) caps concurrent devices. Both can be set via environment or `config.py`.
- `REMEMBER_COOKIE_SAMESITE` and `REMEMBER_COOKIE_SECURE` inherit from app config to support hardened deployments.
- **React/Electron login flows must persist a device identifier** (stored in `localStorage` in the web UI and in the legacy Jinja template via a hidden input). The identifier is sanitized to 64 ASCII chars server-side.
- API clients automatically send their identifier through the `X-Device-Id` header (configured in `frontend/src/utils/api.ts`). This ensures that server-side fingerprinting works for every request, not just the login POST body.

### Migration & Compatibility Notes

- Existing `remember_token` cookies are still honored. When presented, the backend transparently creates a `RememberSession`, reuses the legacy token as the first rotating secret, and clears the old cookie so future logins rely on the new mechanism.
- Session rows are automatically pruned/marked revoked when a device logs out, when fingerprints mismatch, or when TTL expires.
- Because tokens are hashed in the database, leaked backups do not expose reusable browser secrets.
- Security logging captures device id + fingerprint context for both successful rotations and revocations, enabling admins to investigate suspicious remember-me events.

---

## Legacy Implementation Reference (Pre-November 2025)

> The sections below describe the original single-cookie design. They remain for historical context and to explain the legacy upgrade path that is still available for older offline clients.

### Legacy Overview

This archival section documents the original single-cookie remember-me implementation that stored one token per user in the `users` table for roughly 30 days. All of the material below still applies to offline clients that have not yet upgraded and explains how the legacy cookie behaves before it is auto-migrated into a managed `RememberSession`.

### Legacy Features

### ✅ Implemented Features

1. **Persistent Authentication Token**
   - Secure, cryptographically random 32-byte token stored in database
   - 30-day expiration period from last use
   - Automatic expiration extension on each use (rolling 30-day window)

2. **Automatic Login**
   - Transparent auto-login via `@app.before_request` handler
   - Works for both web and Electron offline applications
   - No manual intervention required after initial "Remember Me" selection

3. **Cookie-Based Storage**
   - HttpOnly cookie (prevents JavaScript access - XSS protection)
   - SameSite=Lax (CSRF protection)
   - 30-day max-age matching token expiration
   - Automatically cleared on manual logout

4. **Security Logging**
   - All auto-logins logged with `auto_login_success` event (severity 0)
   - All manual logouts clear tokens and log `logout` event
   - Invalid/expired token attempts logged (no event, just debug log)

5. **User Preference**
   - Per-user `remember_enabled` flag in database
   - User can opt-in or opt-out via checkbox on login form
   - Preference persists across logins

6. **Graceful Degradation**
   - If token is invalid/expired, user is redirected to login (no error)
   - If database is unavailable, feature fails silently (no crash)
   - Errors logged for debugging but don't break user experience

---

### Legacy Architecture

### Database Schema

The `users` table includes these fields (already in schema):

```sql
remember_token TEXT,                -- Secure random token
remember_token_expiration TIMESTAMP,  -- UTC expiration datetime
remember_enabled BOOLEAN DEFAULT 0     -- User preference flag
```

### Token Generation

```python
def generate_remember_token(self):
    """Generate a new remember token for persistent authentication"""
    import secrets
    token = secrets.token_urlsafe(32)
    self.remember_token = token
    self.remember_token_expiration = datetime.utcnow() + timedelta(days=30)
```

- Uses `secrets.token_urlsafe(32)` for cryptographically secure randomness
- 32 bytes = 256 bits of entropy
- URL-safe base64 encoding (no special characters in cookie)

### Token Verification

```python
def verify_remember_token(self, token):
    """Verify if the provided remember token is valid and not expired"""
    if not self.remember_token or not self.remember_token_expiration:
        return False
    
    # Safely parse the expiration datetime
    expiration_dt = safe_parse_datetime_field(self.remember_token_expiration)
    if not expiration_dt:
        return False
        
    # Check if token matches and hasn't expired
    if self.remember_token == token and datetime.utcnow() < expiration_dt:
        return True
    return False
```

- Constant-time string comparison (via Python's `==` for strings)
- Datetime parsing with fallback for various formats
- Expiration check against UTC now
### Auto-Login Flow

```mermaid
graph TD
    A[Request arrives] --> B{User authenticated?}
    B -->|Yes| C[Continue to route]
    B -->|No| D{remember_token cookie present?}
    D -->|No| E[Continue to route - may redirect to login]
    D -->|Yes| F[Query User.find_by_remember_token]
    F --> G{Token valid & not expired?}
    G -->|No| H[Clear cookie, continue to route]
    G -->|Yes| I[login_user with remember=True]
    I --> J[Log auto_login_success event]
    J --> K[Extend token expiration +30 days]
    K --> L[Continue to route - now authenticated]
```

### Cookie Security

```python
resp.set_cookie('remember_token', token, 
                max_age=30*24*60*60,  # 30 days in seconds
                httponly=True,         # Prevent JavaScript access
                samesite='Lax')        # CSRF protection
```

**Security Properties:**
- **HttpOnly:** Cookie cannot be accessed by JavaScript, preventing XSS attacks from stealing tokens
- **SameSite=Lax:** Cookie is only sent on same-site requests and top-level navigation (CSRF protection)
- **No Secure flag:** Allows testing on localhost (add `secure=True` in production with HTTPS)
- **30-day max-age:** Browser automatically deletes cookie after 30 days

---

### Legacy Usage

#### On Login Page:
1. Enter username and password
2. Check the **"Remember me (private device only)"** checkbox
3. Click "Sign In"
4. Token is automatically set and stored in cookie

- Works across browser sessions (even after closing browser)
- Token is cleared from database and cookie
- ❌ **Never use on shared/public computers**
- ✅ **Always manually logout on shared devices**

### For Developers

#### Testing Auto-Login:
```bash
# 1. Login with "Remember Me" checked
# 2. Check cookie in browser DevTools (Application > Cookies)
#    - Name: remember_token
#    - Value: random string (32+ chars)
#    - HttpOnly: ✓
#    - SameSite: Lax
#    - Expires: ~30 days from now

# 3. Close browser completely
# 4. Reopen and navigate to app
# 5. Should be automatically logged in (no login screen)

# 6. Check database:
SELECT id, username, remember_token, remember_token_expiration, remember_enabled 
FROM users 
WHERE id = <your_user_id>;

# 7. Check security logs:
SELECT * FROM security_events 
WHERE event_type = 'auto_login_success' 

```

### Legacy Key Takeaways

1. **Rolling 30-Day Window:** Legacy tokens extend their expiration on every use, so active users rarely see the login screen.
2. **Inactive Sessions Expire:** Users who stay away for ~30 days must re-authenticate, which naturally prunes stale cookies.
3. **Secure by Design:** HttpOnly, SameSite cookies plus server-side expiration checks prevent theft/CSRF from reusing the legacy token.
4. **Seamless UX:** When the legacy cookie validates, the before-request hook logs the user in without extra prompts.
5. **Audit Trail:** Every successful auto-login produces a `auto_login_success` log entry for investigations.
6. **Graceful Failure:** Invalid or expired tokens simply fall back to the login page; no user-facing errors are shown.

#### Debugging:
```python
# In app.py, the before_request handler logs:
app.logger.info(f"Auto-login successful for user_id={user.id} via remember token")
app.logger.debug("Invalid or expired remember token, will clear cookie")
app.logger.error(f"Error during remember token check: {e}")

# Enable debug logging in development:
app.logger.setLevel(logging.DEBUG)
```

---

### Legacy Security Considerations

### ✅ Security Features

1. **Cryptographically Secure Tokens**
   - `secrets.token_urlsafe(32)` = 256 bits of entropy
   - Infeasible to brute force (2^256 combinations)
   - No predictable patterns

2. **HttpOnly Cookies**
   - Prevents XSS attacks from stealing tokens via JavaScript
   - Token only accessible by server, not client-side code

3. **SameSite Protection**
   - Prevents CSRF attacks
   - Cookie only sent on same-site requests

4. **Automatic Expiration**
   - 30-day rolling window (extends on each use)
   - Tokens automatically expire after 30 days of inactivity
   - Database enforces expiration (not just cookie)

5. **Manual Logout Clears All Tokens**
   - Immediately invalidates remember token in database
   - Clears cookie from browser
   - Forces re-authentication

6. **Security Event Logging**
   - All auto-logins logged for audit trail
   - Severity 0 (info) - routine operation
   - Includes IP address for forensics

### ⚠️ Potential Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Physical device theft** | Attacker gains access until token expires | • Educate users: only use on private devices<br>• 30-day expiration limits exposure<br>• Admin can manually revoke tokens via database |
| **Cookie theft via malware** | Attacker can impersonate user | • HttpOnly prevents JavaScript access<br>• SameSite prevents CSRF<br>• Security event logging for forensics |
| **Token not invalidated on password change** | Old token still valid after password reset | **TODO:** Add token invalidation on password change |
| **No IP address binding** | Token works from any IP | Intentional (users may travel, change networks)<br>Security events log IP for forensics |
| **No device fingerprinting** | Token works on any browser | Intentional (users may use multiple browsers)<br>Could add in future if needed |

### 🔒 Recommended Enhancements (Future)

1. **Invalidate tokens on password change**
   ```python
   def set_password(self, password):
       self.password_hash = generate_password_hash(password)
       self.clear_remember_token()  # Force re-login after password change
   ```

2. **Multiple device support with device tracking**
   - Store multiple tokens per user (one per device)
   - Track device info (user agent, last IP, last used)
   - Allow users to view/revoke active devices

3. **Suspicious activity detection**
   - Flag auto-logins from new countries/IPs
   - Email user on first auto-login from new location
   - Option to require password re-entry on suspicious login

4. **Admin token revocation**
   - Admin dashboard to view active remember tokens
   - Bulk revocation (e.g., "logout all users")
   - Per-user revocation

---

### Legacy Configuration

### Environment Variables

No additional environment variables needed. Feature uses existing:
- `USER_FIELD_ENCRYPTION_KEY` - For username/email encryption (already configured)
- `DATABASE_URL` - For database connection (already configured)

### Feature Flags

None currently. Feature is always enabled if user checks "Remember Me" box.

**Optional:** Add app setting to globally disable feature:
```python
# In admin panel or config:
AppSetting.set('remember_me_enabled', '0')  # Disable globally

# In before_request handler:
if AppSetting.get('remember_me_enabled', '1') == '0':
    return  # Skip auto-login check
```

---

### Legacy Platform-Specific Behavior

### Web Application (Flask)
- Cookies stored in browser's cookie jar
- Works across browser sessions (persistent cookies)
- Cleared when user clears browser data

### Electron Offline Application
- Cookies stored in Electron's session storage
- Persists across app restarts
- Location: `<user_data>/Cookies` (platform-specific)
  - Windows: `%APPDATA%/amrs-maintenance-tracker/Cookies`
  - macOS: `~/Library/Application Support/amrs-maintenance-tracker/Cookies`
  - Linux: `~/.config/amrs-maintenance-tracker/Cookies`

**Note:** Electron automatically handles cookie persistence. No additional configuration needed.

---

### Legacy Testing Checklist

### Manual Testing

- [ ] **Web - Initial Login with Remember Me**
  - Login with "Remember Me" checked
  - Verify cookie set in browser (DevTools > Application > Cookies)
  - Verify token in database (`remember_token`, `remember_token_expiration` populated)
  - Verify `remember_enabled = 1`

- [ ] **Web - Auto-Login After Browser Restart**
  - Close browser completely
  - Reopen and navigate to app
  - Should bypass login screen and go straight to dashboard
  - Check security logs for `auto_login_success` event

- [ ] **Web - Token Expiration Extension**
  - Note initial `remember_token_expiration` value
  - Trigger auto-login
  - Check database - expiration should be extended +30 days from now

- [ ] **Web - Manual Logout**
  - Click "Logout"
  - Verify cookie cleared (DevTools > Application > Cookies)
  - Verify token cleared in database (`remember_token = NULL`)
  - Verify next visit requires login

- [ ] **Web - Login Without Remember Me**
  - Login without checking box
  - Verify no cookie set
  - Verify `remember_enabled = 0` in database
  - Close browser, reopen - should require login

- [ ] **Electron - Auto-Login**
  - Login in Electron app with "Remember Me"
  - Close app completely
  - Reopen - should auto-login to dashboard

- [ ] **Electron - Logout**
  - Logout in Electron app
  - Reopen - should show login screen

### Automated Testing

```python
# test_remember_me.py
import unittest
from app import app, db
from models import User
from datetime import datetime, timedelta

class TestRememberMe(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        self.app_context.pop()
    
    def test_generate_remember_token(self):
        """Test token generation creates valid token"""
        user = User.query.first()
        token = user.generate_remember_token()
        
        self.assertIsNotNone(token)
        self.assertEqual(len(token), 43)  # URL-safe base64 of 32 bytes
        self.assertEqual(user.remember_token, token)
        self.assertIsNotNone(user.remember_token_expiration)
        
        # Check expiration is ~30 days from now (within 1 minute tolerance)
        expected_expiration = datetime.utcnow() + timedelta(days=30)
        diff = abs((user.remember_token_expiration - expected_expiration).total_seconds())
        self.assertLess(diff, 60)  # Within 1 minute
    
    def test_verify_remember_token(self):
        """Test token verification"""
        user = User.query.first()
        token = user.generate_remember_token()
        
        # Valid token
        self.assertTrue(user.verify_remember_token(token))
        
        # Invalid token
        self.assertFalse(user.verify_remember_token("invalid_token"))
        
        # Expired token
        user.remember_token_expiration = datetime.utcnow() - timedelta(days=1)
        self.assertFalse(user.verify_remember_token(token))
    
    def test_clear_remember_token(self):
        """Test token clearing"""
        user = User.query.first()
        user.generate_remember_token()
        
        user.clear_remember_token()
        
        self.assertIsNone(user.remember_token)
        self.assertIsNone(user.remember_token_expiration)
    
    def test_find_by_remember_token(self):
        """Test finding user by token"""
        user = User.query.first()
        token = user.generate_remember_token()
        db.session.commit()
        
        # Valid token
        found_user = User.find_by_remember_token(token)
        self.assertEqual(found_user.id, user.id)
        
        # Invalid token
        found_user = User.find_by_remember_token("invalid_token")
        self.assertIsNone(found_user)
    
    def test_login_with_remember_me(self):
        """Test login with remember me checkbox"""
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass',
            'remember': 'on'
        }, follow_redirects=True)
        
        # Check cookie set
        self.assertIn('remember_token', [c.name for c in self.client.cookie_jar])
        
        # Check database
        user = User.query.filter_by(username_hash=hash_value('testuser')).first()
        self.assertTrue(user.remember_enabled)
        self.assertIsNotNone(user.remember_token)

if __name__ == '__main__':
    unittest.main()
```

---

## Maintenance

### Database Cleanup

Old/expired tokens are automatically invalidated by expiration check. However, for database hygiene:

```sql
-- Clear expired tokens (monthly cron job)
UPDATE users 
SET remember_token = NULL, 
    remember_token_expiration = NULL 
WHERE remember_token_expiration < datetime('now', 'utc');

-- Count users with active remember tokens
SELECT COUNT(*) FROM users 
WHERE remember_token IS NOT NULL 
AND remember_token_expiration > datetime('now', 'utc');

-- Revoke all remember tokens (emergency)
UPDATE users 
SET remember_token = NULL, 
    remember_token_expiration = NULL;
```

### Monitoring

```sql
-- Track auto-login frequency
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as auto_logins
FROM security_events 
WHERE event_type = 'auto_login_success'
GROUP BY DATE(timestamp)
ORDER BY date DESC
LIMIT 30;

-- Find users with oldest tokens (potential security risk)
SELECT 
    id,
    username,
    remember_token_expiration,
    JULIANDAY('now') - JULIANDAY(remember_token_expiration) as days_until_expiry
FROM users 
WHERE remember_token IS NOT NULL
ORDER BY remember_token_expiration ASC
LIMIT 20;
```

---

## Troubleshooting

### Issue: Auto-login not working

**Symptoms:** User checks "Remember Me" but still sees login screen on next visit.

**Diagnosis:**
1. Check browser cookies: DevTools > Application > Cookies
   - Is `remember_token` present?
   - Is it expired?
2. Check database:
   ```sql
   SELECT remember_token, remember_token_expiration, remember_enabled 
   FROM users WHERE id = <user_id>;
   ```
3. Check server logs for errors in `check_remember_token()` handler

**Common Causes:**
- User cleared browser cookies/data
- Token expired (>30 days since last use)
- Database connection issue during auto-login check
- `remember_enabled = 0` (user didn't check box or unchecked later)

**Fix:**
- Have user login again with "Remember Me" checked
- Check server logs for exceptions

### Issue: Cookie not setting on login

**Symptoms:** Login succeeds but no `remember_token` cookie in browser.

**Diagnosis:**
1. Check if "Remember Me" box was checked
2. Check response headers for `Set-Cookie`
3. Check database - is token generated?

**Common Causes:**
- User didn't check "Remember Me" box
- Response redirect happening before cookie set (check code order)
- Browser blocking cookies (privacy settings)

**Fix:**
- Ensure `resp.set_cookie()` is called BEFORE `return resp`
- Check browser privacy/cookie settings

### Issue: Token not expiring

**Symptoms:** User can auto-login even months later.

**Diagnosis:**
- Check `remember_token_expiration` in database
- Check if expiration is being extended on each auto-login

**Common Cause:**
- Token expiration is extended +30 days on each use (by design)
- This is a "rolling window" - user must be inactive for 30 days to expire

**Fix:**
- This is expected behavior (rolling 30-day window)
- For forced logout, admin must manually clear token in database

---

## Deployment Checklist

Before deploying to production:

- [ ] **Environment variables configured**
  - `USER_FIELD_ENCRYPTION_KEY` set
  - `DATABASE_URL` set correctly

- [ ] **Database schema updated**
  - Run migrations to add remember token columns (already exists)

- [ ] **HTTPS enabled** (recommended for production)
  - Add `secure=True` to cookie if using HTTPS:
    ```python
    resp.set_cookie('remember_token', token, 
                    max_age=30*24*60*60, 
                    httponly=True, 
                    samesite='Lax',
                    secure=True)  # Only sent over HTTPS
    ```

- [ ] **Security logging enabled**
  - Verify `auto_login_success` events are being logged

- [ ] **User education**
  - Document "Remember Me" feature in user guide
  - Warn users about using on shared devices

- [ ] **Monitor auto-login rate**
  - Check security events for unusual patterns
  - Alert on high auto-login failure rate

---

## Related Documentation

- **Security Event Logging:** `SECURITY_LOGGING_IMPLEMENTATION.md`
- **Database Schema:** `models.py` (User model lines 300-450)
- **Login Flow:** `app.py` (lines 6994-7100)
- **User Authentication:** Flask-Login documentation

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-15  
**Author:** Auto-Login System Implementation  
**Status:** ✅ Production Ready
