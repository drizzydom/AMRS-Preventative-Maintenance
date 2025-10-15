# Windows Installer Fix - Critical Missing Files

**Date:** October 14, 2025  
**Issue:** Windows installer not functioning on standard Windows installations  
**Status:** ✅ Fixed

---

## Problem Description

The Windows installer (both Win7 and Win10 variants) was failing to function on standard Windows installations, making the application ineligible for deployment.

---

## Root Cause Analysis

### Critical Issue: Missing `main.js`

The `electron-builder-win7.js` configuration was **missing `main.js`** in the `files` array. This is the entry point for Electron applications - without it, the application cannot start at all.

**Impact:** Installer would complete successfully, but the application would immediately crash on launch with no visible UI.

### Secondary Issues

1. **Missing critical configuration files:**
   - `package.json` - Required for Electron to understand app metadata
   - `app-package.json` - Application-specific package configuration
   - `latest.yml` - Required for auto-update functionality
   - `versions.json` - Version tracking for updates
   - `main-preload.js` - Preload script for main window

2. **Missing `asarUnpack` section:**
   - Python files were packaged into ASAR archive
   - ASAR archives can't be executed directly
   - Python interpreter couldn't find/execute bundled scripts

3. **Missing `api_utils.py`:**
   - New security helper module created during security hardening
   - Required by `api_endpoints.py` for sanitization
   - Missing from ALL platform builds (Win7, Win10, macOS, Linux)

---

## Files Modified

### 1. `electron-builder-win7.js`
**Changes:**
- ✅ Added `main.js` to files array (CRITICAL)
- ✅ Added `main-preload.js` to files array
- ✅ Added `package.json`, `app-package.json`, `latest.yml`, `versions.json`
- ✅ Added `asarUnpack` section with Python files and YAML files
- ✅ Added `api_utils.py` to both files and asarUnpack sections

### 2. `electron-builder-win10.js`
**Changes:**
- ✅ Added `api_utils.py` to both files and asarUnpack sections
- Note: Already had `main.js` and other critical files

### 3. `electron-builder-macos.js`
**Changes:**
- ✅ Added `api_utils.py` to both files and asarUnpack sections

### 4. `electron-builder-linux.js`
**Changes:**
- ✅ Added `api_utils.py` to both files and asarUnpack sections

---

## Configuration Structure (Fixed)

### Critical Files Section
```javascript
files: [
  "main.js",              // ✅ Entry point for Electron
  "main-preload.js",      // ✅ Preload for main window
  "preload.js",           // ✅ Preload for renderer
  "splash-preload.js",    // ✅ Splash screen preload
  "package.json",         // ✅ App metadata
  "app-package.json",     // ✅ App-specific config
  "latest.yml",           // ✅ Auto-update manifest
  "versions.json",        // ✅ Version tracking
  "*.yml",                // ✅ All YAML config files
  
  // Python application files
  "app.py",
  "api_utils.py",         // ✅ NEW: Security helper (was missing)
  "api_endpoints.py",
  // ... all other Python files
  
  // Static assets
  "templates/**/*",
  "static/**/*",
  "assets/**/*",
  
  // Dependencies
  "node_modules/**/*",
  "requirements.txt"
]
```

### ASAR Unpacking Section
```javascript
asarUnpack: [
  // Config files that need to be accessible
  "package.json",
  "app-package.json",
  "latest.yml",
  "versions.json",
  "**/*.yml",
  "**/*.yaml",
  
  // ALL Python files (must be unpacked to execute)
  "**/*.py",
  "requirements.txt",
  
  // Templates and static assets
  "templates/**/*",
  "static/**/*"
]
```

### Python Bundling
```javascript
extraResources: [
  {
    from: "windows-python/python",  // Embedded Python installation
    to: "python"                     // Copied to resources/python
  }
]
```

---

## Why These Files Are Critical

### `main.js` (MOST CRITICAL)
- **Purpose:** Entry point for Electron application
- **Without it:** Application fails to start with no error message
- **Contains:** App initialization, window management, Python subprocess spawning, update checking

### `package.json`
- **Purpose:** Electron app metadata and configuration
- **Without it:** Electron doesn't know app name, version, dependencies
- **Contains:** App ID, version, main script path, dependencies

### `asarUnpack` Section
- **Purpose:** Extract certain files from ASAR archive to filesystem
- **Why needed:** Python interpreter can't execute scripts inside ASAR
- **Without it:** Python subprocess fails to find app.py

### `api_utils.py`
- **Purpose:** Centralized security sanitization helpers
- **Without it:** Login and API endpoints crash with ImportError
- **Contains:** `prepare_user_for_response()`, `redact_dict_for_logging()`

---

## Testing Checklist

### Before Building Installer
- [x] Verify `windows-python/python/python.exe` exists
- [x] Verify all Python files are in both `files` and `asarUnpack` arrays
- [x] Verify `main.js` is in `files` array
- [x] Verify `api_utils.py` is included in all platform configs

### After Building Installer
- [ ] Install on clean Windows 10/11 machine
- [ ] Verify application launches without errors
- [ ] Check splash screen appears during startup
- [ ] Verify Python dependencies install successfully
- [ ] Confirm application window opens and loads UI
- [ ] Test login functionality (requires `api_utils.py`)
- [ ] Test auto-update check (requires `latest.yml`)

### Runtime Validation
- [ ] Check logs at `%TEMP%\amrs-maintenance-tracker.log`
- [ ] Verify no "Cannot find module 'main.js'" errors
- [ ] Verify no "Cannot find module 'api_utils'" errors
- [ ] Verify Python subprocess starts successfully
- [ ] Confirm Flask server responds on localhost:10000

---

## Build Commands

### Development Build (testing)
```bash
npm run build:win10
```

### Production Builds
```bash
# Windows 10+ (modern)
npm run build:win10

# Windows 7/8 (legacy - not recommended for new deployments)
# Note: Electron 28 may have limited Win7 support
npm run build:win10  # Use this for all Windows versions
```

---

## Platform Compatibility

### Windows 10+
- ✅ Fully supported
- ✅ Uses modern Electron 28.3.3
- ✅ NSIS installer with custom install directory
- ✅ Auto-updates supported

### Windows 7/8 (Legacy)
- ⚠️ Limited support
- ⚠️ May require additional runtime dependencies (vcruntime140.dll)
- ⚠️ Electron 28 support for Windows 7 is deprecated
- **Recommendation:** Target Windows 10+ only for new deployments

---

## Common Installer Issues & Solutions

### Issue: "Application won't start after installation"
**Cause:** Missing `main.js`  
**Solution:** Verify `main.js` is in `files` array ✅ FIXED

### Issue: "Cannot find module 'api_utils'"
**Cause:** Missing new security helper module  
**Solution:** Add `api_utils.py` to build config ✅ FIXED

### Issue: "Python script not found"
**Cause:** Python files not unpacked from ASAR  
**Solution:** Verify `**/*.py` in `asarUnpack` ✅ FIXED

### Issue: "Auto-update not working"
**Cause:** Missing `latest.yml`  
**Solution:** Add to files and asarUnpack ✅ FIXED

---

## Deployment Recommendations

1. **Always test installers on clean VM** before deploying to users
2. **Verify Python bundling** - check `windows-python/python/python.exe` exists
3. **Test on target OS versions** - ideally Windows 10, 11, and Server 2019/2022
4. **Monitor first-run logs** - Check `%TEMP%\amrs-maintenance-tracker.log`
5. **Provide fallback** - Include manual Python installer link in documentation

---

## Files Changed Summary

| File | Changes | Impact |
|------|---------|--------|
| `electron-builder-win7.js` | +10 files, +asarUnpack section | 🔴 Critical - was completely broken |
| `electron-builder-win10.js` | +1 file (`api_utils.py`) | 🟡 High - login would crash |
| `electron-builder-macos.js` | +1 file (`api_utils.py`) | 🟡 High - login would crash |
| `electron-builder-linux.js` | +1 file (`api_utils.py`) | 🟡 High - login would crash |

---

## Related Issues Fixed

This fix also resolves:
- ✅ Login errors after security hardening (missing `api_utils.py`)
- ✅ Auto-update functionality (missing `latest.yml`)
- ✅ Version tracking (missing `versions.json`)
- ✅ Python execution errors (missing asarUnpack)

---

**Fixed by:** GitHub Copilot  
**Review status:** Pending user validation  
**Deployment status:** Ready for testing - requires rebuild
