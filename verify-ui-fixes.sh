#!/bin/bash

# UI and Dark Mode Fix Verification Script
# Date: October 21, 2025
# Purpose: Verify all CSS files are in place and properly configured

echo "=========================================="
echo "UI & Dark Mode Fix Verification"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}✗ Error: Not in the correct directory. Please run from project root.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Running from project root${NC}"
echo ""

# Check for new CSS files
echo "Checking for new CSS files..."
echo ""

CSS_FILES=(
    "static/css/dark-mode-comprehensive-fix.css"
    "static/css/layout-positioning-fix.css"
)

ALL_FOUND=true

for file in "${CSS_FILES[@]}"; do
    if [ -f "$file" ]; then
        SIZE=$(wc -c < "$file" | tr -d ' ')
        LINES=$(wc -l < "$file" | tr -d ' ')
        echo -e "${GREEN}✓ Found: $file${NC}"
        echo "  Size: $SIZE bytes, Lines: $LINES"
    else
        echo -e "${RED}✗ Missing: $file${NC}"
        ALL_FOUND=false
    fi
done

echo ""

# Check if files are referenced in base.html
echo "Checking base.html references..."
echo ""

BASE_HTML="templates/base.html"

if [ -f "$BASE_HTML" ]; then
    echo -e "${GREEN}✓ Found: $BASE_HTML${NC}"
    
    if grep -q "dark-mode-comprehensive-fix.css" "$BASE_HTML"; then
        echo -e "${GREEN}✓ dark-mode-comprehensive-fix.css is referenced${NC}"
    else
        echo -e "${RED}✗ dark-mode-comprehensive-fix.css is NOT referenced${NC}"
        ALL_FOUND=false
    fi
    
    if grep -q "layout-positioning-fix.css" "$BASE_HTML"; then
        echo -e "${GREEN}✓ layout-positioning-fix.css is referenced${NC}"
    else
        echo -e "${RED}✗ layout-positioning-fix.css is NOT referenced${NC}"
        ALL_FOUND=false
    fi
else
    echo -e "${RED}✗ Missing: $BASE_HTML${NC}"
    ALL_FOUND=false
fi

echo ""

# Check for CSS syntax errors (basic check)
echo "Performing basic CSS validation..."
echo ""

for file in "${CSS_FILES[@]}"; do
    if [ -f "$file" ]; then
        # Count opening and closing braces
        OPEN_BRACES=$(grep -o '{' "$file" | wc -l | tr -d ' ')
        CLOSE_BRACES=$(grep -o '}' "$file" | wc -l | tr -d ' ')
        
        if [ "$OPEN_BRACES" -eq "$CLOSE_BRACES" ]; then
            echo -e "${GREEN}✓ $file: Braces balanced ($OPEN_BRACES pairs)${NC}"
        else
            echo -e "${RED}✗ $file: Braces imbalanced (Open: $OPEN_BRACES, Close: $CLOSE_BRACES)${NC}"
            ALL_FOUND=false
        fi
    fi
done

echo ""

# Check for documentation
echo "Checking documentation..."
echo ""

DOC_FILE="UI_DARK_MODE_FIX_SUMMARY.md"

if [ -f "$DOC_FILE" ]; then
    LINES=$(wc -l < "$DOC_FILE" | tr -d ' ')
    echo -e "${GREEN}✓ Found: $DOC_FILE ($LINES lines)${NC}"
else
    echo -e "${YELLOW}⚠ Missing: $DOC_FILE${NC}"
fi

echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""

if [ "$ALL_FOUND" = true ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start your Flask development server:"
    echo "   python app.py"
    echo ""
    echo "2. Open your browser to http://localhost:5050"
    echo ""
    echo "3. Test the following:"
    echo "   - Toggle dark mode (button in navbar)"
    echo "   - Check table headers are orange with white text"
    echo "   - Verify no white space above navbar"
    echo "   - Scroll page and confirm sidebar follows (desktop)"
    echo "   - Check cards display properly in dark mode"
    echo ""
    echo "4. Review the testing checklist in:"
    echo "   UI_DARK_MODE_FIX_SUMMARY.md"
else
    echo -e "${RED}✗ Some checks failed. Please review the issues above.${NC}"
    exit 1
fi

echo ""
echo "=========================================="
