# Data Display Issues - Diagnostic and Fixes

**Date:** January 6, 2025  
**Issues:** Maintenance page not loading data, Users page showing encrypted values

---

## Changes Made

### 1. Enhanced Maintenance Page Data Loading

**File:** `frontend/src/pages/Maintenance.tsx`

**Changes:**
- Added detailed console logging to track API responses
- Added null/undefined checks for response data
- Added informative message when no maintenance tasks are found
- Improved error handling with detailed error messages
- Added empty state UI with helpful guidance

**Empty State Message:**
```
No Maintenance Tasks Found
Maintenance tasks are automatically generated from parts with scheduled maintenance.
To see tasks here, add parts to machines and set their maintenance schedules.
```

**Why Maintenance Page Might Be Empty:**
The maintenance tasks are generated from the `parts` table where:
1. A part must have `next_maintenance` date set
2. The part must be associated with a machine
3. Tasks are auto-generated based on maintenance schedule

**To Populate Maintenance Tasks:**
1. Go to Machines page
2. Select a machine
3. Add/edit parts for that machine
4. Set maintenance schedule for each part (frequency + unit)
5. Maintenance page will automatically show upcoming/overdue tasks

---

### 2. Enhanced User Decryption Debugging

**Files Modified:**
- `api_v1.py` - Enhanced logging in `/users` endpoint
- `models.py` - Improved `decrypt_value()` function

**Changes to `api_v1.py`:**
- Added detailed logging for each user's decryption process
- Logs success/failure for username and email decryption
- Detects if values appear to be encrypted (length > 50 chars)
- Provides stack traces for decryption failures

**Changes to `models.py` `decrypt_value()`:**
- Added type checking (returns non-strings as-is)
- Added empty string handling
- Enhanced error handling with specific exception types:
  - `InvalidToken` - Wrong encryption key or corrupted data → Returns `[ENCRYPTED:...]` placeholder
  - `AttributeError/ValueError/UnicodeDecodeError` - Likely plaintext → Returns as-is
  - Other exceptions → Returns `[ERROR:...]` with error message
- Added logging for all failure cases

**Diagnostic Output:**
When you start the app, check the logs for messages like:
```
Processing user X: raw _username length=XXX
User X: Successfully decrypted username: XXXXX
User X: Successfully decrypted email: XXXXX
```

Or error messages like:
```
Failed to decrypt username for user X: [error details]
User X: Value appears to be encrypted (length=XXX)
```

---

### 3. Created Diagnostic Script

**File:** `diagnose_user_encryption.py` (NEW)

**Purpose:** Standalone script to diagnose user encryption issues

**Usage:**
```bash
python3 diagnose_user_encryption.py
```

**What It Checks:**
- Encryption key availability
- All users in database
- Raw column values (length, first 50 chars)
- Decryption success/failure for each user
- Manual decryption attempts
- Reports which users have issues

---

## Root Cause Analysis

### Users Page Issue

The Users page shows encrypted values when:

1. **Wrong Encryption Key**
   - The data was encrypted with key A
   - The app is trying to decrypt with key B
   - Solution: Ensure `USER_FIELD_ENCRYPTION_KEY` environment variable matches the key used during user creation

2. **Missing Encryption Key**
   - No encryption key is set
   - System falls back to a temporary key (different each run)
   - Solution: Set proper encryption key in environment or keyring

3. **Data Not Encrypted**
   - Legacy data stored as plaintext
   - System tries to decrypt but fails
   - Solution: The enhanced `decrypt_value()` now handles this gracefully

### Maintenance Page Issue

The Maintenance page is empty when:

1. **No Parts with Schedules**
   - Database has machines but no parts
   - Or parts exist but have no `next_maintenance` date set
   - Solution: Add parts to machines with maintenance schedules

2. **API Connection Issue**
   - Frontend can't reach backend API
   - Solution: Check browser console for API errors

3. **Database Structure Issue**
   - Required tables missing
   - Solution: Run database migrations

---

## Testing Steps

### Test Maintenance Page

1. **Open Browser Console** (F12)
2. **Navigate to Maintenance page**
3. **Check Console Logs:**
   ```
   Maintenance API response: { data: [...] }
   Loaded X maintenance tasks
   ```
4. **If you see "No maintenance tasks found":**
   - This is expected if database has no parts with schedules
   - Go to Machines → select machine → Add Parts → Set maintenance schedule
   - Return to Maintenance page and refresh

### Test Users Page

1. **Check Application Logs** (where Flask is running)
2. **Navigate to Users page**
3. **Look for logs like:**
   ```
   Processing user 1: raw _username length=XXX
   User 1: Successfully decrypted username: admin
   User 1: Successfully decrypted email: admin@example.com
   ```
4. **If you see decryption failures:**
   - Note the error message
   - Check if encryption key is set correctly
   - Run diagnostic script: `python3 diagnose_user_encryption.py`

### Run Diagnostic Script

```bash
cd /path/to/AMRS-Preventative-Maintenance
python3 diagnose_user_encryption.py
```

**Expected Output:**
```
==========================================
USER DATA ENCRYPTION DIAGNOSTIC
==========================================
✓ Encryption key loaded successfully

Found 3 users in database
==========================================

User ID: 1
  Role: Administrator
  Is Admin: True

  Raw _username column value:
    Length: 152
    First 50 chars: gAAAAABm8xY...

  ✓ Decrypted username: admin
  ✓ Decrypted email: admin@example.com
```

**If Encryption Fails:**
```
✗ Failed to decrypt username: [error details]
User 1: Value appears to be encrypted (length=152)
```

This means the encryption key doesn't match. You need to either:
1. Find the correct encryption key used when creating users
2. Or re-create users with the current encryption key

---

## Solution Paths

### If Users Show `[ENCRYPTED:...]`

**Option 1: Find Correct Encryption Key**
1. Check if key is in keyring:
   ```bash
   python3 -c "import keyring; print(keyring.get_password('amrs_pm_macos', 'USER_FIELD_ENCRYPTION_KEY'))"
   ```
2. Check environment variables:
   ```bash
   echo $USER_FIELD_ENCRYPTION_KEY
   ```
3. Set the correct key before starting app

**Option 2: Re-create Users**
1. Export user list (usernames, emails, roles)
2. Delete encrypted users from database
3. Ensure encryption key is set
4. Re-create users through UI or script
5. Users will be encrypted with current key

### If Maintenance Page is Empty

**Option 1: Add Test Data**
1. Navigate to Machines page
2. Add a machine (if none exist)
3. Click on machine → Add Part
4. Fill in part details
5. **Important:** Set maintenance schedule:
   - Maintenance Frequency: e.g., "30"
   - Maintenance Unit: e.g., "days"
   - Last Maintenance: recent date
6. Save part
7. Go to Maintenance page - task should appear

**Option 2: Check Database**
```sql
SELECT p.id, p.name, p.next_maintenance, m.name as machine_name
FROM parts p
JOIN machines m ON p.machine_id = m.id
WHERE p.next_maintenance IS NOT NULL;
```

If query returns rows, data exists but API might have issue.
If query returns nothing, no parts have maintenance schedules.

---

## Next Steps

1. **Start the application**
2. **Check logs** for decryption messages
3. **Test both pages** and check console/logs
4. **Run diagnostic script** if user decryption fails
5. **Report findings:**
   - What do you see on Users page? (usernames or `[ENCRYPTED:...]`?)
   - What do you see on Maintenance page? (tasks or empty state?)
   - Any error messages in console or logs?

---

## Files Changed

1. ✅ `frontend/src/pages/Maintenance.tsx` - Enhanced logging + empty state
2. ✅ `api_v1.py` - Enhanced user decryption logging
3. ✅ `models.py` - Improved `decrypt_value()` with better error handling
4. ✅ `diagnose_user_encryption.py` - NEW diagnostic script

**Frontend Build:** ✅ Successfully compiled (no errors)

---

**End of Report**
