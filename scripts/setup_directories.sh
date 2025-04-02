#!/bin/bash
# =============================================================================
# AMRS Directory Setup Script
# This script creates all necessary directories for the AMRS system
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Directory Setup${NC}"
echo "===================="
echo

# Check if root directory is provided as argument
if [ -n "$1" ]; then
    ROOT_DIR="$1"
    echo "Using provided root directory: $ROOT_DIR"
else
    # Default directory for Synology
    if [ -d "/volume1" ]; then
        ROOT_DIR="/volume1/docker/amrs-data"
    else
        ROOT_DIR="$HOME/amrs-data"
    fi
    echo "Using default root directory: $ROOT_DIR"
fi

# Function to create directory and handle errors
create_dir() {
    local dir="$1"
    echo "Creating directory: $dir"
    mkdir -p "$dir"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to create directory: $dir${NC}"
        return 1
    else
        echo -e "${GREEN}✓ Created directory: $dir${NC}"
        return 0
    fi
}

# Create main directories
echo -e "${BOLD}1. Creating main directories...${NC}"
create_dir "$ROOT_DIR" || { echo "Cannot create root directory. Exiting."; exit 1; }
create_dir "$ROOT_DIR/templates"
create_dir "$ROOT_DIR/static" 
create_dir "$ROOT_DIR/nginx"
create_dir "$ROOT_DIR/ssl"
echo "Main directories created."
echo

# Create subdirectories
echo -e "${BOLD}2. Creating subdirectories...${NC}"
create_dir "$ROOT_DIR/static/css"
create_dir "$ROOT_DIR/static/js"
create_dir "$ROOT_DIR/static/images"
create_dir "$ROOT_DIR/nginx/conf.d"
create_dir "$ROOT_DIR/data"
create_dir "$ROOT_DIR/logs"
create_dir "$ROOT_DIR/backup"
echo "Subdirectories created."
echo

# Set appropriate permissions
echo -e "${BOLD}3. Setting permissions...${NC}"

# First try with more restrictive permissions
chmod 755 "$ROOT_DIR"
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}! Could not set 755 permissions, trying 777...${NC}"
    chmod -R 777 "$ROOT_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to set any permissions on $ROOT_DIR${NC}"
        echo "This might cause issues with file access."
    else
        echo -e "${YELLOW}! Set permissive 777 permissions on $ROOT_DIR${NC}"
        echo "This is less secure but ensures the application will work."
    fi
else
    # More specific permissions for sensitive areas
    chmod 777 "$ROOT_DIR/data"  # Database directory needs write access
    chmod 755 "$ROOT_DIR/ssl"   # SSL directory should be more restricted
    
    echo -e "${GREEN}✓ Set appropriate permissions on directories${NC}"
fi
echo

# Create a tracking file to indicate successful setup
echo "Setup completed at $(date)" > "$ROOT_DIR/.setup_complete"

echo -e "${GREEN}${BOLD}Directory setup complete!${NC}"
echo "Root directory: $ROOT_DIR"
echo
echo "You can proceed with the next step of the installation."

# Output the root directory for use by other scripts
echo "$ROOT_DIR"
