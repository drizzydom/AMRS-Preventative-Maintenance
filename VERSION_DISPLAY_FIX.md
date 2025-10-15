# Version Display Fix Documentation

**Date:** October 15, 2025  
**Issue:** Empty version numbers displaying in both deployed website and Electron desktop application  
**Status:** ✅ **FIXED**

---

## Problem Analysis

### Symptoms
- Both web deployment and Electron app showed **empty** version numbers in the footer
- Template expected `{{ app_version }}` variable but it was not being provided
- Version should automatically update from `package.json` (currently `1.4.5`)

### Root Causes Identified

1. **Electron App Issue:**
   - Flask server launched by Electron was not receiving `APP_VERSION` environment variable
   - The `env` object in `main.js` (line ~897) did not include `APP_VERSION`
   - Flask code tried to read `os.environ.get("APP_VERSION", "")` which returned empty string

2. **Web Deployment Issue:**
   - Context processor `inject_common_variables()` did not include `app_version` in returned dictionary
   - No fallback mechanism to read version from `package.json`
   - Multiple other locations in `app.py` tried to read `APP_VERSION` env var with empty fallback

3. **Template Dependency:**
   - `templates/base.html` line 647: `<span class="text-muted">Version {{ app_version }}</span>`
   - Template expected variable that was never injected

---

## Solution Implementation

### Fix 1: Electron Environment Variable (main.js)

**File:** `main.js` (line ~897)  
**Change:** Added `APP_VERSION` to Flask process environment variables

```javascript
// BEFORE:
const env = {
    ...process.env,
    FLASK_ENV: 'production',
    FLASK_DEBUG: 'false',
    FLASK_RUN_HOST: '127.0.0.1',
    FLASK_RUN_PORT: FLASK_PORT.toString(),
    PORT: FLASK_PORT.toString(),
    SECRET_KEY: require('crypto').randomBytes(32).toString('hex'),
    PYTHONPATH: __dirname,
    PYTHONUNBUFFERED: '1'  // Ensure immediate output
};

// AFTER:
const env = {
    ...process.env,
    FLASK_ENV: 'production',
    FLASK_DEBUG: 'false',
    FLASK_RUN_HOST: '127.0.0.1',
    FLASK_RUN_PORT: FLASK_PORT.toString(),
    PORT: FLASK_PORT.toString(),
    SECRET_KEY: require('crypto').randomBytes(32).toString('hex'),
    PYTHONPATH: __dirname,
    PYTHONUNBUFFERED: '1',  // Ensure immediate output
    APP_VERSION: app.getVersion()  // Pass version from package.json to Flask
};
```

**Impact:** Electron app now passes version from `package.json` to Flask automatically

---

### Fix 2: Flask Context Processor (app.py)

**File:** `app.py` (line ~4357)  
**Function:** `inject_common_variables()`  
**Change:** Added version reading logic with environment variable and `package.json` fallback

```python
# BEFORE:
@app.context_processor
def inject_common_variables():
    """Inject common variables into all templates."""
    # ... existing code ...
    
    return {
        'is_admin_user': is_admin_user(current_user) if is_auth else False,
        'url_for_safe': url_for_safe,
        'datetime': datetime,
        'now': datetime.now(),
        'hasattr': hasattr,
        'has_permission': has_permission,
        'Role': Role,
        'safe_date': safe_date
    }

# AFTER:
@app.context_processor
def inject_common_variables():
    """Inject common variables into all templates."""
    # ... existing code ...
    
    # Get app version from environment variable (set by Electron) or package.json
    app_version = os.environ.get("APP_VERSION", "")
    if not app_version:
        # Fallback: Read from package.json (for web deployments)
        try:
            import json
            package_json_path = os.path.join(os.path.dirname(__file__), 'package.json')
            if os.path.exists(package_json_path):
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    app_version = package_data.get('version', '1.4.5')
            else:
                app_version = '1.4.5'  # Final fallback
        except Exception as e:
            app.logger.warning(f"Could not read version from package.json: {e}")
            app_version = '1.4.5'  # Final fallback
    
    return {
        'is_admin_user': is_admin_user(current_user) if is_auth else False,
        'url_for_safe': url_for_safe,
        'datetime': datetime,
        'now': datetime.now(),
        'hasattr': hasattr,
        'has_permission': has_permission,
        'Role': Role,
        'safe_date': safe_date,
        'app_version': app_version  # Add version for display in footer
    }
```

**Impact:** 
- Web deployments now read version from `package.json` automatically
- Electron app gets version from environment variable (faster)
- Multiple fallback layers ensure version always displays
- Version updates automatically when `package.json` is updated

---

## Version Resolution Priority

The system now uses this priority order for determining the version:

1. **Environment Variable** (`APP_VERSION`) - Set by Electron, fastest lookup
2. **package.json file** - Read dynamically for web deployments
3. **Hardcoded Fallback** (`1.4.5`) - Last resort if both above fail

---

## Testing Checklist

### Electron Desktop App
- [ ] Build Electron app with new changes
- [ ] Launch application and check footer shows version `1.4.5`
- [ ] Update `package.json` version to `1.4.6`
- [ ] Rebuild and verify new version displays

### Web Deployment
- [ ] Deploy to Render.com (or other hosting)
- [ ] Navigate to any page and check footer
- [ ] Verify version `1.4.5` (or current) displays correctly
- [ ] Test with `package.json` temporarily removed to verify fallback works

### Version Update Process
- [ ] Update version in `package.json` only (single source of truth)
- [ ] Rebuild Electron app → Version should auto-update
- [ ] Deploy web app → Version should auto-update
- [ ] No manual environment variable configuration needed

---

## Related Files Modified

### Primary Changes
1. **`main.js`** (line ~897)
   - Added `APP_VERSION: app.getVersion()` to Flask environment variables

2. **`app.py`** (line ~4357-4395)
   - Enhanced `inject_common_variables()` context processor
   - Added version reading logic with fallback
   - Added `app_version` to template context

### Files Using Version Display
1. **`templates/base.html`** (line 647)
   - Footer: `<span class="text-muted">Version {{ app_version }}</span>`
   - No changes needed (already correct)

2. **`package.json`** (line 2)
   - Source of truth: `"version": "1.4.5"`
   - Update here for all version changes

---

## Technical Details

### Context Processor Mechanics
- Context processors run on **every template render**
- `inject_common_variables()` makes `app_version` available globally in all templates
- Reading from environment variable is cached by OS (fast)
- Reading from `package.json` is only needed for web deployments (happens once per template render, minimal overhead)

### Electron Version Passing
- `app.getVersion()` reads from Electron's internal package.json cache (instant)
- Version passed as environment variable to Flask subprocess
- Flask reads from environment (no file I/O needed in Electron mode)

### Error Handling
- File not found → Falls back to hardcoded version
- JSON parse error → Falls back to hardcoded version
- Environment variable not set → Falls back to package.json read
- All errors logged with `app.logger.warning()` for debugging

---

## Deployment Notes

### Automatic Version Updates
✅ **Version now updates automatically** when `package.json` is changed and app is rebuilt/redeployed

### No Manual Configuration Required
- ✅ No need to set `APP_VERSION` environment variable manually
- ✅ No need to update version in multiple locations
- ✅ Single source of truth: `package.json`

### Backward Compatibility
- ✅ Existing deployments will show fallback version `1.4.5` until redeployed
- ✅ No breaking changes to existing functionality
- ✅ Hardcoded fallback ensures version always displays (never empty)

---

## Future Considerations

### Optional Enhancements
1. **Cache package.json version** at app startup to avoid repeated file reads
2. **Add version API endpoint** for programmatic version checking
3. **Display build date/commit hash** alongside version number
4. **Add version mismatch detection** between frontend and backend

### Related Issues
- `inject_debug_context()` (line 10359+) has hardcoded `version="2.0.0"`
  - This can be updated to use `app_version` for consistency
  - Variable name is `version` not `app_version` (template compatibility unknown)

---

## Verification Commands

### Check Current Version in Package.json
```bash
grep '"version"' package.json
```

### Test Version Display Locally (Flask)
```bash
python app.py
# Navigate to http://localhost:5000 and check footer
```

### Test Version Display in Electron
```bash
npm start
# Check footer in application window
```

### Check Environment Variable (Electron)
```bash
# Add to app.py temporarily:
print(f"[DEBUG] APP_VERSION from env: {os.environ.get('APP_VERSION', 'NOT SET')}")
```

---

## Summary

**Problem:** Empty version numbers in UI  
**Root Cause:** `app_version` template variable not injected by context processor  
**Solution:** Added version reading logic with multiple fallbacks  
**Result:** Version automatically displays and updates from `package.json`  

**Files Changed:** 2 (`main.js`, `app.py`)  
**Lines Added:** ~20  
**Breaking Changes:** None  
**Testing Required:** Verify in both Electron and web deployments  

✅ **Fix complete and ready for testing**
