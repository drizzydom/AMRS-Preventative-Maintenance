#!/bin/bash
# =============================================================================
# AMRS Permission Fix Script
# This script corrects permissions on data files
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Permission Fix Script${NC}"
echo "=========================="
echo

# Check if data directory is provided as argument
if [ -n "$1" ]; then
    DATA_DIR="$1"
    echo "Using provided data directory: $DATA_DIR"
else
    # Default directory for Synology
    if [ -d "/volume1" ]; then
        DATA_DIR="/volume1/docker/amrs-data"
    else
        DATA_DIR="$HOME/amrs-data"
    fi
    echo "Using default data directory: $DATA_DIR"
fi

# Check if directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}✗ Data directory does not exist: $DATA_DIR${NC}"
    exit 1
fi

# Fix main directory permission
echo -e "${BOLD}1. Setting base directory permissions...${NC}"
chmod -R 777 "$DATA_DIR"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Set directory permissions to 777 for maximum compatibility${NC}"
    echo "This is less secure but ensures the application will work."
else
    echo -e "${RED}✗ Failed to set permissions${NC}"
fi
echo

# Fix database file permissions
echo -e "${BOLD}2. Setting database file permissions...${NC}"
# Create data subdirectory with proper permissions
mkdir -p "$DATA_DIR/data"
chmod 777 "$DATA_DIR/data"

for db_path in "$DATA_DIR/app.db" "$DATA_DIR/data/app.db"; do
    touch "$db_path" 2>/dev/null
    chmod 666 "$db_path" 2>/dev/null
    echo -e "${GREEN}✓ Set database permissions for: $db_path${NC}"
done

# Try to set ownership as well (may require sudo)
if command -v sudo &> /dev/null; then
    echo "Attempting to set proper ownership (may require sudo password)"
    sudo chown -R 1000:1000 "$DATA_DIR" 2>/dev/null || true
fi
echo

# Fix SSL directory permissions
echo -e "${BOLD}3. Setting SSL certificate permissions...${NC}"
if [ -d "$DATA_DIR/ssl" ]; then
    chmod 755 "$DATA_DIR/ssl"
    
    # Check for certificate files
    if [ -f "$DATA_DIR/ssl/fullchain.pem" ]; then
        chmod 644 "$DATA_DIR/ssl/fullchain.pem"
        echo -e "${GREEN}✓ Set fullchain.pem permissions to 644 (rw-r--r--)${NC}"
    fi
    
    if [ -f "$DATA_DIR/ssl/privkey.pem" ]; then
        chmod 600 "$DATA_DIR/ssl/privkey.pem"
        echo -e "${GREEN}✓ Set privkey.pem permissions to 600 (rw-------)${NC}"
    fi
else
    echo -e "${YELLOW}! SSL directory not found${NC}"
    mkdir -p "$DATA_DIR/ssl"
    chmod 755 "$DATA_DIR/ssl"
    echo "Created SSL directory with proper permissions."
fi

# Fix template and static directories
echo -e "${BOLD}4. Setting template and static file permissions...${NC}"
if [ -d "$DATA_DIR/templates" ]; then
    chmod -R 755 "$DATA_DIR/templates"
    echo -e "${GREEN}✓ Set template directory permissions${NC}"
fi

if [ -d "$DATA_DIR/static" ]; then
    chmod -R 755 "$DATA_DIR/static"
    echo -e "${GREEN}✓ Set static files directory permissions${NC}"
fi

# Fix script permissions
echo -e "${BOLD}5. Setting script file permissions...${NC}"
for script in "$DATA_DIR"/*.{py,sh}; do
    if [ -f "$script" ]; then
        chmod 755 "$script"
        echo -e "${GREEN}✓ Made executable: $script${NC}"
    fi
done

echo
echo -e "${GREEN}${BOLD}Permission fixes completed!${NC}"
echo "Directory permissions have been corrected."
echo "This should resolve any file access issues with the application."
