#!/bin/bash

echo "=== AMRS Version Management Demo ==="
echo ""

# Show current state
echo "Current package.json version:"
grep '"version"' package.json | head -1

echo ""
echo "Current versions.json content:"
cat versions.json
echo ""

echo "=== Two Approaches for Version Management ==="
echo ""

echo "APPROACH 1: AUTOMATIC (Current Setup)"
echo "- postbuild scripts automatically update versions.json"
echo "- When you build, updates are immediately available"
echo "- Workflow:"
echo "  1. Change package.json version to 1.4.5"  
echo "  2. Run 'npm run build:all'"
echo "  3. versions.json automatically updates to 1.4.5"
echo "  4. Users immediately see update prompts"
echo ""

echo "APPROACH 2: MANUAL CONTROL"
echo "- You control when updates are offered"
echo "- Build and test before enabling updates"
echo "- Workflow:"
echo "  1. Change package.json version to 1.4.5"
echo "  2. Run 'npm run build:all' (no auto-update)"
echo "  3. Test the 1.4.5 build"
echo "  4. When ready: 'npm run set:latest 1.4.5'"
echo "  5. Now users see update prompts"
echo ""

echo "Which approach do you prefer?"
echo "  A) Automatic - updates offered immediately after build"
echo "  B) Manual - you control when updates are offered"
echo ""

read -p "Enter A or B: " choice

if [ "$choice" = "A" ] || [ "$choice" = "a" ]; then
    echo ""
    echo "✓ AUTOMATIC approach is already configured!"
    echo "  postbuild:win10, postbuild:mac, postbuild:linux scripts will auto-update versions.json"
    echo ""
    echo "To test: Change package.json version and run 'npm run build:win10'"
    
elif [ "$choice" = "B" ] || [ "$choice" = "b" ]; then
    echo ""
    echo "Switching to MANUAL approach..."
    echo "Removing postbuild scripts from package.json..."
    
    # Remove postbuild scripts (manual approach)
    sed -i '' '/postbuild:/d' package.json
    
    echo "✓ MANUAL approach configured!"
    echo "  Build scripts won't auto-update versions.json"
    echo "  Use 'npm run set:latest VERSION' when ready to offer updates"
    
else
    echo "Invalid choice. Keeping current configuration."
fi

echo ""
echo "=== Current Configuration ==="
grep -E "postbuild:|build:" package.json || echo "No postbuild scripts (Manual mode)"
