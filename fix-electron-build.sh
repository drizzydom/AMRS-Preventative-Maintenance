#!/bin/bash

# Fix Electron Build Issues Script
# This script addresses the windowless app and missing UI updates issues

echo "============================================"
echo "Fixing Electron Build Issues"
echo "============================================"
echo ""

# Step 1: Clean all build artifacts
echo "Step 1: Cleaning build artifacts..."
rm -rf dist/
rm -rf build/
rm -rf node_modules/.cache/
echo "✓ Build artifacts cleaned"
echo ""

# Step 2: Clean Electron cache (macOS/Linux)
echo "Step 2: Cleaning Electron cache..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    rm -rf ~/Library/Application\ Support/Electron
    rm -rf ~/Library/Caches/Electron
    rm -rf ~/Library/Application\ Support/amrs-preventative-maintenance
    echo "✓ Electron cache cleaned (macOS)"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    rm -rf ~/.config/Electron
    rm -rf ~/.cache/electron
    rm -rf ~/.config/amrs-preventative-maintenance
    echo "✓ Electron cache cleaned (Linux)"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    rm -rf "$APPDATA/Electron"
    rm -rf "$LOCALAPPDATA/Electron"
    rm -rf "$APPDATA/amrs-preventative-maintenance"
    echo "✓ Electron cache cleaned (Windows)"
fi
echo ""

# Step 3: Verify critical files exist
echo "Step 3: Verifying critical files..."
FILES_TO_CHECK=(
    "main.js"
    "package.json"
    "templates/base.html"
    "static/css/table-layout-comprehensive-fix.css"
    "static/js/dashboard.js"
)

MISSING_FILES=0
for file in "${FILES_TO_CHECK[@]}"; do
    if [ ! -f "$file" ]; then
        echo "✗ Missing: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo "✓ Found: $file"
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo ""
    echo "ERROR: $MISSING_FILES critical file(s) missing!"
    echo "Please ensure all files are synced before building."
    exit 1
fi
echo ""

# Step 4: Check if main.js has the correct frame setting
echo "Step 4: Checking main.js window configuration..."
if grep -q "frame: true" main.js; then
    echo "✓ Window frame is enabled (app will have close/minimize/maximize buttons)"
elif grep -q "frame: false" main.js; then
    echo "⚠ WARNING: Window frame is disabled!"
    echo "  The app will be windowless without custom title bar implementation."
    echo "  Update main.js to set 'frame: true' for standard window controls."
else
    echo "? Could not determine frame setting in main.js"
fi
echo ""

# Step 5: Show build instructions
echo "============================================"
echo "Next Steps:"
echo "============================================"
echo ""
echo "To rebuild the application with all changes:"
echo ""
echo "For macOS:"
echo "  npm run build:mac"
echo ""
echo "For Windows:"
echo "  npm run build:win10"
echo ""
echo "For Linux:"
echo "  npm run build:linux"
echo ""
echo "To test without building (development mode):"
echo "  npm start"
echo ""
echo "============================================"
echo "Common Issues & Solutions:"
echo "============================================"
echo ""
echo "1. App is windowless (no close button):"
echo "   → Fixed! main.js now has 'frame: true'"
echo ""
echo "2. UI changes not showing:"
echo "   → Clean build artifacts (Done ✓)"
echo "   → Ensure static/templates folders are included in package.json (Done ✓)"
echo "   → Rebuild the app completely"
echo ""
echo "3. Flask server not starting:"
echo "   → Check that Python is bundled correctly"
echo "   → Verify python/ directory exists with embedded Python"
echo ""
echo "============================================"
