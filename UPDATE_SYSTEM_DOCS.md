# AMRS Auto-Update System - Intelligent Version Detection

## Overview
The AMRS auto-update system now uses intelligent version detection instead of hardcoded target versions. This eliminates unnecessary update prompts and provides proper control over when updates are offered.

## How It Works

### 1. App Version Detection
- App bundles `app-package.json` with current version (1.4.4)
- Flask server reads app version from bundled files
- Multiple fallback methods ensure version is always detected

### 2. Server-Side Available Version Control
- `versions.json` file controls what version server advertises as "latest"
- Update server compares app version vs. available version
- Only offers updates when newer version is actually available

### 3. Smart Update Logic
```
IF available_version > app_version:
    Serve update metadata for available_version
ELSE:
    Serve current version (no update prompt)
```

## Usage

### For Development (No Updates)
```bash
npm run set:latest 1.4.4
```
- App version: 1.4.4
- Available version: 1.4.4
- Result: No update prompts

### When New Version is Released
```bash
npm run set:latest 1.4.5
```
- App version: 1.4.4
- Available version: 1.4.5
- Result: Update prompts appear

### Build Process
```bash
npm run build:all
```
Automatically:
1. Generates `app-package.json` with current version
2. Creates `latest.yml` with current version
3. Bundles both files in the installer

## Files

### Generated Files
- `app-package.json` - Minimal package.json for bundling
- `latest.yml` - Current version metadata for bundling
- `versions.json` - Controls what server advertises as latest

### Configuration Files
- `package.json` - Source of truth for app version
- `electron-builder-*.js` - Ensures files are bundled correctly

## Benefits

### ✅ Before (Problems)
- Hardcoded `UPDATE_TARGET_VERSION=1.4.5` in environment
- App always thinks update is available
- No way to control when updates are offered
- Excessive keychain prompts on macOS

### ✅ After (Solution)
- Server dynamically determines latest available version
- App only prompts when update is actually available
- Simple control over update availability
- Proper version comparison logic

## Deployment Workflow

### 1. Development Phase
```bash
# Ensure no updates are offered during development
npm run set:latest 1.4.4
npm run build:all
```

### 2. Release New Version
```bash
# Update package.json version to 1.4.5
# Build new installers
npm run build:all

# Deploy installers to server/storage
# Enable updates for existing 1.4.4 users
npm run set:latest 1.4.5
```

### 3. Stop Offering Updates (if needed)
```bash
# Disable updates temporarily
npm run set:latest 1.4.4
```

## Testing

Run the comprehensive test suite:
```bash
./test-update-system.sh
```

This tests all scenarios:
- No updates available
- Updates available
- Version comparison logic
- File generation and detection

## Technical Details

### Version Comparison
Uses proper semantic version comparison via Python's `packaging` library:
```python
from packaging import version as version_parser
if version_parser.parse(available) > version_parser.parse(current):
    # Offer update
```

### File Inclusion
All necessary files are properly bundled via `asarUnpack` in electron-builder:
- `app-package.json` - App version detection
- `versions.json` - Available version control
- `latest.yml` - Update metadata template

### Fallback Logic
Multiple fallback methods ensure system works even if files are missing:
1. Read from `versions.json`
2. Check environment variables
3. Use current app version as fallback

This robust design eliminates the keychain prompt issues while providing reliable auto-update functionality.
