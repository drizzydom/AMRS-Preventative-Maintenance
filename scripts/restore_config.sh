#!/bin/bash
# =============================================================================
# AMRS Configuration Restore Script
# This script restores configuration files and database from a backup
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Configuration Restore${NC}"
echo "=========================="
echo

# Check if backup file is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No backup file specified${NC}"
    echo "Usage: $0 <backup_file.tar.gz> [data_directory]"
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

# Check if data directory is provided as argument
if [ -n "$2" ]; then
    DATA_DIR="$2"
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

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Create temporary directory for extraction
TEMP_RESTORE_DIR=$(mktemp -d)

echo -e "${BOLD}1. Stopping running containers...${NC}"
if docker ps | grep -q 'amrs'; then
    docker-compose down 2>/dev/null || docker stop $(docker ps -q -f "name=amrs") 2>/dev/null
    echo -e "${GREEN}✓ Containers stopped${NC}"
else
    echo -e "${YELLOW}! No AMRS containers found running${NC}"
fi
echo

echo -e "${BOLD}2. Extracting backup archive...${NC}"
tar -xzf "$BACKUP_FILE" -C "$TEMP_RESTORE_DIR"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup extracted${NC}"
else
    echo -e "${RED}✗ Failed to extract backup${NC}"
    rm -rf "$TEMP_RESTORE_DIR"
    exit 1
fi
echo

echo -e "${BOLD}3. Creating backup of current configuration...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$DATA_DIR/backup"
CURRENT_BACKUP="$BACKUP_DIR/pre_restore_backup_$TIMESTAMP.tar.gz"
mkdir -p "$BACKUP_DIR"

# Quick backup of critical files
tar -czf "$CURRENT_BACKUP" -C "$DATA_DIR" nginx ssl templates 2>/dev/null
echo -e "${GREEN}✓ Current configuration backed up to $CURRENT_BACKUP${NC}"
echo

echo -e "${BOLD}4. Restoring configuration files...${NC}"

# Restore Nginx configuration
if [ -d "$TEMP_RESTORE_DIR/nginx" ]; then
    echo "Restoring Nginx configuration..."
    mkdir -p "$DATA_DIR/nginx"
    cp -r "$TEMP_RESTORE_DIR/nginx/"* "$DATA_DIR/nginx/"
    echo -e "${GREEN}✓ Nginx configuration restored${NC}"
else
    echo -e "${YELLOW}! No Nginx configuration found in backup${NC}"
fi

# Restore SSL certificates
if [ -d "$TEMP_RESTORE_DIR/ssl" ]; then
    echo "Restoring SSL certificates..."
    mkdir -p "$DATA_DIR/ssl"
    cp -r "$TEMP_RESTORE_DIR/ssl/"* "$DATA_DIR/ssl/"
    chmod 644 "$DATA_DIR/ssl/fullchain.pem" 2>/dev/null
    chmod 600 "$DATA_DIR/ssl/privkey.pem" 2>/dev/null
    echo -e "${GREEN}✓ SSL certificates restored${NC}"
else
    echo -e "${YELLOW}! No SSL certificates found in backup${NC}"
fi

# Restore templates
if [ -d "$TEMP_RESTORE_DIR/templates" ]; then
    echo "Restoring templates..."
    mkdir -p "$DATA_DIR/templates"
    cp -r "$TEMP_RESTORE_DIR/templates/"* "$DATA_DIR/templates/"
    echo -e "${GREEN}✓ Templates restored${NC}"
else
    echo -e "${YELLOW}! No templates found in backup${NC}"
fi

# Restore scripts
if [ -d "$TEMP_RESTORE_DIR/scripts" ]; then
    echo "Restoring scripts..."
    # Copy scripts to data directory
    find "$TEMP_RESTORE_DIR/scripts" -type f \( -name "*.py" -o -name "*.sh" \) -exec cp {} "$DATA_DIR/" \;
    # Make shell scripts executable
    find "$DATA_DIR" -name "*.sh" -exec chmod +x {} \;
    echo -e "${GREEN}✓ Scripts restored${NC}"
else
    echo -e "${YELLOW}! No scripts found in backup${NC}"
fi

# Restore docker-compose.yml if it exists
if [ -f "$TEMP_RESTORE_DIR/docker-compose.yml" ]; then
    echo "Restoring docker-compose.yml..."
    cp "$TEMP_RESTORE_DIR/docker-compose.yml" "$DATA_DIR/../docker-compose.yml"
    echo -e "${GREEN}✓ docker-compose.yml restored${NC}"
else
    echo -e "${YELLOW}! docker-compose.yml not found in backup${NC}"
fi
echo

echo -e "${BOLD}5. Restoring database...${NC}"
# Find the database backup
DB_BACKUP=$(find "$TEMP_RESTORE_DIR" -name "app_db_*.db" | head -1)

if [ -n "$DB_BACKUP" ]; then
    # Create data directory if it doesn't exist
    mkdir -p "$DATA_DIR/data"
    
    # Create backup of current database if it exists
    if [ -f "$DATA_DIR/data/app.db" ]; then
        cp "$DATA_DIR/data/app.db" "$DATA_DIR/data/app.db.bak_$TIMESTAMP"
        echo -e "${YELLOW}! Created backup of existing database${NC}"
    fi
    
    # Copy the database
    cp "$DB_BACKUP" "$DATA_DIR/data/app.db"
    chmod 666 "$DATA_DIR/data/app.db" # Ensure proper permissions
    
    echo -e "${GREEN}✓ Database restored${NC}"
else
    echo -e "${YELLOW}! No database backup found${NC}"
fi
echo

# Clean up temporary directory
rm -rf "$TEMP_RESTORE_DIR"

echo -e "${BOLD}6. Setting appropriate permissions...${NC}"
find "$DATA_DIR/nginx" "$DATA_DIR/templates" -type d -exec chmod 755 {} \; 2>/dev/null
find "$DATA_DIR/nginx" "$DATA_DIR/templates" -type f -exec chmod 644 {} \; 2>/dev/null
chmod -R 755 "$DATA_DIR/ssl" 2>/dev/null
echo -e "${GREEN}✓ Permissions set${NC}"
echo

echo -e "${BOLD}7. Starting containers...${NC}"
if [ -f "$DATA_DIR/../docker-compose.yml" ]; then
    cd "$DATA_DIR/.." && docker-compose up -d
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Containers started${NC}"
    else
        echo -e "${RED}✗ Failed to start containers${NC}"
        echo "Try running docker-compose up -d manually"
    fi
else
    echo -e "${YELLOW}! docker-compose.yml not found, cannot start containers automatically${NC}"
    echo "You will need to start the containers manually"
fi

echo
echo -e "${GREEN}${BOLD}Configuration restore completed!${NC}"
echo "The AMRS system has been restored from the backup."
echo
echo "Next steps:"
echo "1. Verify that the system is running correctly"
echo "2. Access the AMRS application in your browser"
echo "3. If there are issues, check the container logs:"
echo "   docker logs amrs-maintenance-tracker"
echo
echo "If you need to revert to the previous configuration, use:"
echo "   ./restore_config.sh $CURRENT_BACKUP $DATA_DIR"
