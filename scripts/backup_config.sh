#!/bin/bash
# =============================================================================
# AMRS Configuration Backup Script
# This script backs up all configuration files and database for the AMRS system
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Configuration Backup${NC}"
echo "========================="
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

# Create timestamp for backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$DATA_DIR/backup"
BACKUP_FILE="$BACKUP_DIR/amrs_backup_$TIMESTAMP.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function to check if container is running
container_running() {
    local name="$1"
    docker ps | grep -q "$name"
    return $?
}

echo -e "${BOLD}1. Creating backup directory...${NC}"
if [ -d "$BACKUP_DIR" ]; then
    echo -e "${GREEN}✓ Backup directory exists: $BACKUP_DIR${NC}"
else
    echo -e "${RED}✗ Failed to create backup directory${NC}"
    exit 1
fi

echo -e "${BOLD}2. Backing up database...${NC}"
DB_BACKUP="$BACKUP_DIR/app_db_$TIMESTAMP.db"

if container_running "amrs-maintenance-tracker"; then
    # Container is running, get database directly from container
    if docker exec amrs-maintenance-tracker bash -c 'cat /app/data/app.db' > "$DB_BACKUP" 2>/dev/null; then
        echo -e "${GREEN}✓ Database backed up from container to $DB_BACKUP${NC}"
    elif docker exec amrs-maintenance-tracker bash -c 'cat /app/app.db' > "$DB_BACKUP" 2>/dev/null; then
        echo -e "${GREEN}✓ Database backed up from alternate location to $DB_BACKUP${NC}"
    else
        echo -e "${YELLOW}! Could not backup database from container${NC}"
        # Try copying from data directory directly
        if [ -f "$DATA_DIR/app.db" ]; then
            cp "$DATA_DIR/app.db" "$DB_BACKUP"
            echo -e "${GREEN}✓ Database backed up from data directory${NC}"
        elif [ -f "$DATA_DIR/data/app.db" ]; then
            cp "$DATA_DIR/data/app.db" "$DB_BACKUP"
            echo -e "${GREEN}✓ Database backed up from data/app.db${NC}"
        else
            echo -e "${RED}✗ Could not find database file${NC}"
        fi
    fi
else
    # Container not running, try to find database file directly
    if [ -f "$DATA_DIR/app.db" ]; then
        cp "$DATA_DIR/app.db" "$DB_BACKUP"
        echo -e "${GREEN}✓ Database backed up from data directory${NC}"
    elif [ -f "$DATA_DIR/data/app.db" ]; then
        cp "$DATA_DIR/data/app.db" "$DB_BACKUP"
        echo -e "${GREEN}✓ Database backed up from data/app.db${NC}"
    else
        echo -e "${RED}✗ Could not find database file${NC}"
    fi
fi

echo -e "${BOLD}3. Backing up configuration files...${NC}"
# Create a temporary directory for the backup
TEMP_BACKUP_DIR=$(mktemp -d)

# Copy important configuration files
echo "Copying nginx configuration..."
if [ -d "$DATA_DIR/nginx" ]; then
    mkdir -p "$TEMP_BACKUP_DIR/nginx"
    cp -r "$DATA_DIR/nginx" "$TEMP_BACKUP_DIR/"
    echo -e "${GREEN}✓ Nginx configuration backed up${NC}"
else
    echo -e "${YELLOW}! Nginx configuration directory not found${NC}"
fi

echo "Copying SSL certificates..."
if [ -d "$DATA_DIR/ssl" ]; then
    mkdir -p "$TEMP_BACKUP_DIR/ssl"
    cp -r "$DATA_DIR/ssl" "$TEMP_BACKUP_DIR/"
    echo -e "${GREEN}✓ SSL certificates backed up${NC}"
else
    echo -e "${YELLOW}! SSL directory not found${NC}"
fi

echo "Copying templates..."
if [ -d "$DATA_DIR/templates" ]; then
    mkdir -p "$TEMP_BACKUP_DIR/templates"
    cp -r "$DATA_DIR/templates" "$TEMP_BACKUP_DIR/"
    echo -e "${GREEN}✓ Templates backed up${NC}"
else
    echo -e "${YELLOW}! Templates directory not found${NC}"
fi

echo "Copying scripts..."
mkdir -p "$TEMP_BACKUP_DIR/scripts"
# Copy all Python and shell scripts
find "$DATA_DIR" -maxdepth 1 -type f \( -name "*.py" -o -name "*.sh" \) -exec cp {} "$TEMP_BACKUP_DIR/scripts/" \;
echo -e "${GREEN}✓ Custom scripts backed up${NC}"

# Copy docker-compose.yml if it exists
if [ -f "$DATA_DIR/../docker-compose.yml" ]; then
    cp "$DATA_DIR/../docker-compose.yml" "$TEMP_BACKUP_DIR/"
    echo -e "${GREEN}✓ docker-compose.yml backed up${NC}"
else
    echo -e "${YELLOW}! docker-compose.yml not found${NC}"
fi

# Copy database backup to temp directory
cp "$DB_BACKUP" "$TEMP_BACKUP_DIR/"

# Create compressed archive
echo -e "${BOLD}4. Creating compressed backup archive...${NC}"
tar -czf "$BACKUP_FILE" -C "$TEMP_BACKUP_DIR" .
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup archive created: $BACKUP_FILE${NC}"
else
    echo -e "${RED}✗ Failed to create backup archive${NC}"
fi

# Cleanup temporary directory
rm -rf "$TEMP_BACKUP_DIR"

# Set appropriate permissions
chmod 644 "$BACKUP_FILE"
echo -e "${GREEN}✓ Set appropriate permissions on backup file${NC}"

# Get backup file size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo
echo -e "${GREEN}${BOLD}Backup completed successfully!${NC}"
echo "Backup file: $BACKUP_FILE"
echo "Backup size: $BACKUP_SIZE"
echo "Database backup: $DB_BACKUP"
echo
echo "To restore from this backup, use the restore_config.sh script:"
echo "./restore_config.sh $BACKUP_FILE $DATA_DIR"
