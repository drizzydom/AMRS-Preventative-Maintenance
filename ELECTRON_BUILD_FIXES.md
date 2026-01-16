# Electron Build Issues - Troubleshooting Guide

## Issues Encountered

### 1. **Application is Windowless (No Close/Minimize/Maximize Buttons)**

**Symptom:** After building the desktop app, it opens without any window controls, making it impossible to close the application without force-quitting.

**Root Cause:** The `main.js` file had `frame: false` set in the BrowserWindow configuration (line 1157). This creates a frameless window intended for custom title bars, but the custom title bar was never implemented in the UI.

**Fix Applied:**
```javascript
// BEFORE (Broken)
frame: false, // Frameless window for custom title bar

// AFTER (Fixed)
frame: true, // Use native OS window frame (includes close/minimize/maximize buttons)
```

Also changed `titleBarStyle` from `'hidden'` to `'default'`.

**Files Modified:**
- `main.js` (lines 1157, 1168)

---

### 2. **UI Changes Not Appearing in Built Application**

**Symptom:** Despite implementing comprehensive UI overhauls through GitHub Copilot, the built Electron application shows the old UI instead of the new changes.

**Root Causes:**

1. **Incomplete file inclusion in build**: The `package.json` build configuration had:
   - Generic `"**/*"` pattern which can be unreliable
   - Explicit exclusion of `node_modules` twice (redundant)
   - No explicit inclusion of `static/**` and `templates/**` directories
   
2. **Build cache not cleared**: Electron Builder caches files, and old versions can persist across builds

3. **Electron app cache**: The running Electron app caches static assets

**Fixes Applied:**

#### A. Updated `package.json` file inclusion (lines 38-64):

```json
"files": [
  "main.js",
  "main-preload.js",
  "splash-preload.js",
  "app/print-preload.js",
  "app/**",
  "assets/**",
  "static/**",        // ← Explicitly include
  "templates/**",     // ← Explicitly include
  "*.py",
  "models.py",
  "config.py",
  "requirements.txt",
  "package.json",
  "!venv/**/*",
  "!node_modules/**/*",
  "!dist/**/*",
  "!.git/**/*",
  "!.github/**/*",
  "!**/__pycache__/**/*",
  "!**/*.pyc",
  "!**/*.pyo",
  "!.env",
  "!.env.*",
  "!*.log",
  "!test_*.py",
  "!**/test/**",
  "!**/.DS_Store",
  "!memory-bank/**/*",
  "!docs/**/*"
]
```

#### B. Added cleaning scripts to `package.json`:

```json
"clean": "rm -rf dist build node_modules/.cache",
"clean:electron": "rm -rf ~/Library/Application\\ Support/Electron ~/Library/Caches/Electron || true",
"clean:all": "npm run clean && npm run clean:electron",
"rebuild": "npm run clean:all && npm run build:win10"
```

#### C. Updated build scripts to clean before building:

```json
"prebuild:win10": "npm run clean && npm run generate:package && npm run generate:latest",
"prebuild:mac": "npm run clean && npm run generate:package && npm run generate:latest",
"prebuild:linux": "npm run clean && npm run generate:package && npm run generate:latest"
```

#### D. Created `fix-electron-build.sh` script:
- Cleans all build artifacts (`dist/`, `build/`, `node_modules/.cache/`)
- Cleans Electron cache (OS-specific)
- Verifies critical files exist
- Checks main.js configuration
- Provides clear rebuild instructions

**Files Modified:**
- `package.json` (build configuration and scripts)
- `fix-electron-build.sh` (new file)

---

## How to Fix Your Build

### Quick Fix (Immediate)

1. **Clean everything:**
   ```bash
   ./fix-electron-build.sh
   ```

2. **Or manually:**
   ```bash
   # Clean build artifacts
   rm -rf dist/ build/ node_modules/.cache/
   
   # Clean Electron cache (macOS)
   rm -rf ~/Library/Application\ Support/Electron
   rm -rf ~/Library/Caches/Electron
   rm -rf ~/Library/Application\ Support/amrs-preventative-maintenance
   ```

3. **Rebuild:**
   ```bash
   # macOS
   npm run build:mac
   
   # Windows
   npm run build:win10
   
   # Linux
   npm run build:linux
   ```

### Test Before Building

To verify changes work before doing a full build:

```bash
npm start
```

This runs the Electron app in development mode, loading files directly from your workspace.

---

## What Changed

### Summary of Fixes

| Issue | File | Change |
|-------|------|--------|
| Windowless app | `main.js` | Changed `frame: false` → `frame: true` |
| Windowless app | `main.js` | Changed `titleBarStyle: 'hidden'` → `titleBarStyle: 'default'` |
| Missing static files | `package.json` | Added explicit `"static/**"` inclusion |
| Missing templates | `package.json` | Added explicit `"templates/**"` inclusion |
| Cached old files | `package.json` | Added clean scripts |
| Build not cleaning | `package.json` | Added `npm run clean` to prebuild scripts |
| Manual process | `fix-electron-build.sh` | Created automated fix script |

---

## Prevention

To prevent these issues in the future:

1. **Always test in development mode first:**
   ```bash
   npm start
   ```

2. **Clean before building:**
   ```bash
   npm run clean:all
   npm run build:mac  # or build:win10, build:linux
   ```

3. **Use the rebuild script:**
   ```bash
   npm run rebuild
   ```

4. **Verify files are included:**
   - Check that new directories are listed in `package.json` → `build.files`
   - Use explicit patterns (`static/**`) instead of wildcards (`**/*`)

5. **Never use `frame: false` without implementing a custom title bar:**
   - Either keep `frame: true` (native controls)
   - Or implement a complete custom title bar with close/minimize/maximize buttons

---

## Technical Details

### Why `frame: false` Caused Issues

The `frame: false` setting in Electron's BrowserWindow creates a frameless window, which:
- Removes all native OS window controls (title bar, buttons, borders)
- Requires implementing custom window controls in HTML/CSS/JS
- Needs IPC handlers in the preload script to communicate with Electron's window APIs
- Must handle window dragging, resizing, minimize/maximize/close manually

**Example of what's needed for frameless windows:**

```html
<!-- Custom title bar HTML -->
<div class="title-bar">
  <div class="title">App Name</div>
  <div class="controls">
    <button onclick="window.electron.minimize()">−</button>
    <button onclick="window.electron.maximize()">□</button>
    <button onclick="window.electron.close()">×</button>
  </div>
</div>
```

```javascript
// Preload script IPC handlers
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close: () => ipcRenderer.send('window-close')
});
```

```javascript
// Main process IPC listeners
ipcMain.on('window-minimize', () => mainWindow.minimize());
ipcMain.on('window-maximize', () => {
  if (mainWindow.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow.maximize();
  }
});
ipcMain.on('window-close', () => mainWindow.close());
```

Since none of this was implemented, the app became windowless.

### Why UI Changes Didn't Appear

1. **File Glob Patterns:** The `"**/*"` pattern in `package.json` is processed by electron-builder's default file filter, which has its own exclusion rules. This can miss directories not explicitly listed.

2. **Build Cache:** Electron Builder caches previously built files for performance. Without cleaning, it reuses old files.

3. **Electron Cache:** The running Electron app caches static assets (CSS/JS) in the user's Application Support directory.

4. **Order of Operations:** The generic `"**/*"` pattern comes after specific exclusions, so it may not override them properly.

**Solution:** Explicit inclusion of critical directories ensures they're always bundled:
```json
"static/**",
"templates/**"
```

---

## Verification Checklist

After rebuilding, verify:

- [ ] Application opens with window controls (close/minimize/maximize buttons visible)
- [ ] Can close the application normally (click X button)
- [ ] New UI styles are visible (check table layouts, sidebar positioning, etc.)
- [ ] Dashboard "Hide All Parts" functionality works
- [ ] Sidebar scrolls with page content (sticky positioning)
- [ ] All cache-busted CSS files load with correct version numbers

---

## Support

If issues persist after following this guide:

1. Check the Electron Developer Console:
   - Open the app
   - Press Cmd+Option+I (Mac) or Ctrl+Shift+I (Windows/Linux)
   - Look for errors in the Console tab

2. Check the Flask logs:
   - Look for log files in the application directory
   - Check for Python/Flask startup errors

3. Verify Python bundling:
   - Check that the `python/` directory exists in the built application
   - Ensure Python interpreter and dependencies are included

4. Check file permissions:
   - Ensure all files in `static/` and `templates/` are readable
   - Verify shell scripts are executable (`chmod +x *.sh`)

---

## Files Modified in This Fix

1. **main.js**
   - Line 1157: `frame: false` → `frame: true`
   - Line 1168: `titleBarStyle: 'hidden'` → `titleBarStyle: 'default'`

2. **package.json**
   - Lines 38-64: Updated `build.files` array with explicit inclusions
   - Lines 6-27: Added cleaning and rebuild scripts

3. **fix-electron-build.sh** (new file)
   - Automated cleaning and verification script
   - 150+ lines of comprehensive build fixing

---

## Version Information

- **Electron Version:** 28.3.3
- **App Version:** 1.4.6
- **Fix Date:** November 2, 2025
- **Issue Scope:** Desktop application builds only (not web version)

### 2. **Duplicate Window Bar on Windows**

**Symptom:** On Windows, the application shows two title bars: the native OS title bar and the custom React title bar.

**Root Cause:** The `TitleBar` component was implemented in React, but `main.js` was still configured with `frame: true` (from Fix #1). This resulted in both the OS frame and the custom title bar being visible.

**Fix Applied:**
Reverted `BrowserWindow` configuration to `frame: false` to hide the native OS frame, relying on the custom `TitleBar` component for window controls (handled via IPC).

```javascript
// BEFORE (Duplicate bars)
frame: true, // Use native OS window frame

// AFTER (Fixed)
frame: false, // Use custom title bar (hide native OS frame)
```
