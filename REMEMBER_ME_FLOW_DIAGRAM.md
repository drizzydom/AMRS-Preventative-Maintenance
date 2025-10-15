# Remember Me Auto-Login Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FIRST LOGIN WITH "REMEMBER ME"                   │
└─────────────────────────────────────────────────────────────────────────┘

User                Browser              Server                Database
  │                    │                    │                      │
  │  Enter credentials │                    │                      │
  │  ✓ Remember Me     │                    │                      │
  │─────────────────>  │                    │                      │
  │                    │  POST /login       │                      │
  │                    │─────────────────>  │                      │
  │                    │                    │  Verify password     │
  │                    │                    │───────────────────>  │
  │                    │                    │  ✓ Password valid    │
  │                    │                    │<─────────────────────│
  │                    │                    │                      │
  │                    │                    │  Generate token      │
  │                    │                    │  (secrets.token_     │
  │                    │                    │   urlsafe(32))       │
  │                    │                    │                      │
  │                    │                    │  Save to database:   │
  │                    │                    │  - remember_token    │
  │                    │                    │  - expiration (+30d) │
  │                    │                    │───────────────────>  │
  │                    │                    │  ✓ Token saved       │
  │                    │                    │<─────────────────────│
  │                    │                    │                      │
  │                    │  Set-Cookie:       │                      │
  │                    │  remember_token=   │                      │
  │                    │  abc123...;        │                      │
  │                    │  HttpOnly;         │                      │
  │                    │  SameSite=Lax;     │                      │
  │                    │  Max-Age=2592000   │                      │
  │                    │<─────────────────  │                      │
  │                    │                    │                      │
  │  Redirect to       │                    │                      │
  │  dashboard         │                    │                      │
  │<─────────────────  │                    │                      │
  │                    │                    │                      │
  │  [Cookie stored    │                    │                      │
  │   in browser]      │                    │                      │
  │                    │                    │                      │


┌─────────────────────────────────────────────────────────────────────────┐
│                    SUBSEQUENT VISIT (AUTO-LOGIN)                         │
└─────────────────────────────────────────────────────────────────────────┘

User                Browser              Server                Database
  │                    │                    │                      │
  │  Open app          │                    │                      │
  │─────────────────>  │                    │                      │
  │                    │  GET /dashboard    │                      │
  │                    │  Cookie:           │                      │
  │                    │  remember_token=   │                      │
  │                    │  abc123...         │                      │
  │                    │─────────────────>  │                      │
  │                    │                    │                      │
  │                    │         @app.before_request               │
  │                    │         check_remember_token()            │
  │                    │                    │                      │
  │                    │                    │  Find user by token  │
  │                    │                    │  & verify expiration │
  │                    │                    │───────────────────>  │
  │                    │                    │  ✓ Token valid       │
  │                    │                    │<─────────────────────│
  │                    │                    │                      │
  │                    │                    │  login_user()        │
  │                    │                    │  [Session created]   │
  │                    │                    │                      │
  │                    │                    │  Log security event: │
  │                    │                    │  "auto_login_success"│
  │                    │                    │───────────────────>  │
  │                    │                    │                      │
  │                    │                    │  Extend expiration   │
  │                    │                    │  to +30 days from now│
  │                    │                    │───────────────────>  │
  │                    │                    │  ✓ Updated           │
  │                    │                    │<─────────────────────│
  │                    │                    │                      │
  │                    │  200 OK            │                      │
  │                    │  Dashboard HTML    │                      │
  │                    │<─────────────────  │                      │
  │                    │                    │                      │
  │  Dashboard         │                    │                      │
  │  displayed         │                    │                      │
  │  (Logged in!)      │                    │                      │
  │<─────────────────  │                    │                      │


┌─────────────────────────────────────────────────────────────────────────┐
│                           MANUAL LOGOUT                                  │
└─────────────────────────────────────────────────────────────────────────┘

User                Browser              Server                Database
  │                    │                    │                      │
  │  Click "Logout"    │                    │                      │
  │─────────────────>  │                    │                      │
  │                    │  GET /logout       │                      │
  │                    │  Cookie:           │                      │
  │                    │  remember_token=   │                      │
  │                    │  abc123...         │                      │
  │                    │─────────────────>  │                      │
  │                    │                    │                      │
  │                    │                    │  Clear token in DB:  │
  │                    │                    │  remember_token=NULL │
  │                    │                    │───────────────────>  │
  │                    │                    │  ✓ Cleared           │
  │                    │                    │<─────────────────────│
  │                    │                    │                      │
  │                    │                    │  Log security event: │
  │                    │                    │  "logout"            │
  │                    │                    │───────────────────>  │
  │                    │                    │                      │
  │                    │                    │  logout_user()       │
  │                    │                    │  [Session destroyed] │
  │                    │                    │                      │
  │                    │  Set-Cookie:       │                      │
  │                    │  remember_token=;  │                      │
  │                    │  expires=0         │                      │
  │                    │  (Clear cookie)    │                      │
  │                    │<─────────────────  │                      │
  │                    │                    │                      │
  │                    │  302 Redirect      │                      │
  │                    │  to /login         │                      │
  │                    │<─────────────────  │                      │
  │                    │                    │                      │
  │  [Cookie deleted   │                    │                      │
  │   from browser]    │                    │                      │
  │                    │                    │                      │
  │  Login page        │                    │                      │
  │  displayed         │                    │                      │
  │<─────────────────  │                    │                      │


┌─────────────────────────────────────────────────────────────────────────┐
│                    EXPIRED TOKEN (Auto-Login Fails)                      │
└─────────────────────────────────────────────────────────────────────────┘

User                Browser              Server                Database
  │                    │                    │                      │
  │  Open app          │                    │                      │
  │  (after 30 days)   │                    │                      │
  │─────────────────>  │                    │                      │
  │                    │  GET /dashboard    │                      │
  │                    │  Cookie:           │                      │
  │                    │  remember_token=   │                      │
  │                    │  abc123...         │                      │
  │                    │─────────────────>  │                      │
  │                    │                    │                      │
  │                    │         @app.before_request               │
  │                    │         check_remember_token()            │
  │                    │                    │                      │
  │                    │                    │  Find user by token  │
  │                    │                    │───────────────────>  │
  │                    │                    │  ✓ Token found       │
  │                    │                    │<─────────────────────│
  │                    │                    │                      │
  │                    │                    │  Check expiration:   │
  │                    │                    │  ✗ EXPIRED!          │
  │                    │                    │  (>30 days old)      │
  │                    │                    │                      │
  │                    │                    │  [Auto-login skipped]│
  │                    │                    │  [No error thrown]   │
  │                    │                    │                      │
  │                    │  302 Redirect      │                      │
  │                    │  to /login         │                      │
  │                    │  (not authenticated)                      │
  │                    │<─────────────────  │                      │
  │                    │                    │                      │
  │  Login page        │                    │                      │
  │  displayed         │                    │                      │
  │  (Must re-login)   │                    │                      │
  │<─────────────────  │                    │                      │


┌─────────────────────────────────────────────────────────────────────────┐
│                         SECURITY FEATURES                                │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────┐
│   Token Security   │
└────────────────────┘
• 256-bit entropy (secrets.token_urlsafe(32))
• Cryptographically secure random generation
• Impossible to guess or brute force
• Unique per user per login

┌────────────────────┐
│  Cookie Security   │
└────────────────────┘
• HttpOnly ────────────> Cannot be accessed by JavaScript (XSS protection)
• SameSite=Lax ────────> Only sent on same-site requests (CSRF protection)
• 30-day Max-Age ──────> Browser auto-deletes after 30 days
• Secure (optional) ───> Only sent over HTTPS (production)

┌────────────────────┐
│ Database Security  │
└────────────────────┘
• Token stored in database alongside user
• Expiration timestamp enforced on server side
• Token cleared on manual logout
• Token invalidated after 30 days of inactivity
• Rolling window: extends +30 days on each use

┌────────────────────┐
│  Audit Logging     │
└────────────────────┘
• "auto_login_success" event logged (severity 0)
• IP address recorded for forensics
• Timestamp of each auto-login
• "logout" event when token cleared
• Queryable for security monitoring

┌────────────────────┐
│ Error Handling     │
└────────────────────┘
• Graceful degradation if token invalid
• No error shown to user (seamless fallback)
• Errors logged for debugging
• Request continues normally if auto-login fails


┌─────────────────────────────────────────────────────────────────────────┐
│                      TOKEN LIFECYCLE (30-DAY ROLLING)                    │
└─────────────────────────────────────────────────────────────────────────┘

Day 0: Login with "Remember Me"
│
├─ Token generated
├─ Expiration: Day 0 + 30 days = Day 30
├─ Cookie set with Max-Age=2592000 (30 days)
│
Day 5: Auto-login
│
├─ Token verified: valid (Day 5 < Day 30)
├─ Expiration extended: Day 5 + 30 days = Day 35
├─ User stays logged in
│
Day 20: Auto-login
│
├─ Token verified: valid (Day 20 < Day 35)
├─ Expiration extended: Day 20 + 30 days = Day 50
├─ User stays logged in
│
Day 60: User inactive for 40 days
│
├─ Token expired (Day 60 > Day 50)
├─ Auto-login fails silently
├─ Redirect to login page
│
User must re-login to get new token

```

---

## Key Takeaways

1. **Rolling 30-Day Window:** Token expiration extends on each use, so active users never have to re-login
2. **Inactive Users Expire:** If user doesn't visit for 30 days, token expires
3. **Secure by Design:** HttpOnly + SameSite + Expiration + Server-side validation
4. **Seamless UX:** Auto-login happens transparently, no user action required
5. **Audit Trail:** All auto-logins logged for security monitoring
6. **Graceful Failure:** Invalid/expired tokens fail silently, no error to user

---

**Diagram Version:** 1.0  
**Last Updated:** October 15, 2025
