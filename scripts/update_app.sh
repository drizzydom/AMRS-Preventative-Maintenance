#!/bin/bash
# =============================================================================
# AMRS Application Update Script
# This script safely updates the AMRS application to a newer version
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Application Update${NC}"
echo "======================="
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

# Get script directory and project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to check if a container needs updating
container_needs_update() {
    local container="$1"
    local current_id=$(docker inspect --format='{{.Id}}' "$container" 2>/dev/null)
    
    if [ -z "$current_id" ]; then
        # Container doesn't exist, needs update
        return 0
    fi
    
    # Get image name from container
    local image_name=$(docker inspect --format='{{.Config.Image}}' "$container")
    
    # Pull the latest image
    docker pull "$image_name" >/dev/null 2>&1
    
    # Get ID of the latest image
    local latest_id=$(docker inspect --format='{{.Id}}' "$image_name")
    
    # Compare IDs
    if [ "$current_id" != "$latest_id" ]; then
        return 0 # Needs update
    else
        return 1 # No update needed
    fi
}

echo -e "${BOLD}1. Creating backup before update...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$DATA_DIR/backup"
BACKUP_FILE="$BACKUP_DIR/pre_update_$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"
if [ -d "$DATA_DIR" ]; then
    # Create quick backup of important files
    tar -czf "$BACKUP_FILE" -C "$DATA_DIR" nginx ssl templates data 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
    else
        echo -e "${YELLOW}! Warning: Backup creation may not be complete${NC}"
    fi
else
    echo -e "${RED}✗ Data directory not found, cannot create backup${NC}"
    echo "Continuing without backup..."
fi
echo

# Check if docker-compose file exists
DOCKER_COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo -e "${RED}Error: docker-compose.yml not found at $DOCKER_COMPOSE_FILE${NC}"
    echo "Please run this script from the project directory containing docker-compose.yml"
    exit 1
fi

echo -e "${BOLD}2. Pulling latest Docker images...${NC}"
cd "$PROJECT_DIR"
docker-compose pull
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully pulled latest images${NC}"
else
    echo -e "${RED}✗ Failed to pull latest images${NC}"
    echo "Continuing with update using locally available images..."
fi
echo

echo -e "${BOLD}3. Checking for code updates...${NC}"
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "Git repository detected, trying to update code..."
    
    # Check for uncommitted changes
    if [ -n "$(git -C "$PROJECT_DIR" status --porcelain)" ]; then
        echo -e "${YELLOW}! Warning: You have uncommitted changes.${NC}"
        read -p "Continue with git pull? (y/n): " GIT_CONTINUE
        if [[ ! "$GIT_CONTINUE" =~ ^[Yy]$ ]]; then
            echo "Skipping code update."
        else
            git -C "$PROJECT_DIR" pull
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ Code updated successfully${NC}"
            else
                echo -e "${RED}✗ Failed to update code${NC}"
            fi
        fi
    else
        # No uncommitted changes, proceed with update
        git -C "$PROJECT_DIR" pull
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Code updated successfully${NC}"
        else
            echo -e "${RED}✗ Failed to update code${NC}"
        fi
    fi
else
    echo -e "${YELLOW}! Not a git repository, skipping code update${NC}"
fi
echo

echo -e "${BOLD}4. Rebuilding the app container...${NC}"
docker-compose build --no-cache app
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ App container rebuilt successfully${NC}"
else
    echo -e "${RED}✗ Failed to rebuild app container${NC}"
    echo "Continuing with update using existing container..."
fi
echo

echo -e "${BOLD}5. Stopping running containers...${NC}"
docker-compose down
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Containers stopped successfully${NC}"
else
    echo -e "${RED}✗ Failed to stop containers properly${NC}"
    echo "Attempting to force stop..."
    docker-compose kill
fi
echo

echo -e "${BOLD}6. Applying any database migrations...${NC}"
echo -e "${YELLOW}! This is where database migrations would run if needed${NC}"
echo "No automatic migrations system implemented yet."
echo "If this update includes database schema changes,"
echo "they will be applied when the container starts."
echo

echo -e "${BOLD}7. Starting updated containers...${NC}"
docker-compose up -d
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Updated containers started successfully${NC}"
else
    echo -e "${RED}✗ Failed to start containers${NC}"
    echo "Please check the logs and try to start containers manually:"
    echo "cd $PROJECT_DIR && docker-compose up -d"
    exit 1
fi
echo

echo -e "${BOLD}8. Running post-update fixes...${NC}"
# Update permissions
find "$DATA_DIR" -name "*.sh" -exec chmod +x {} \; 2>/dev/null
chmod 666 "$DATA_DIR/data/app.db" 2>/dev/null

# Ensure proper permissions on SSL certificates
if [ -d "$DATA_DIR/ssl" ]; then
    chmod 644 "$DATA_DIR/ssl/fullchain.pem" 2>/dev/null
    chmod 600 "$DATA_DIR/ssl/privkey.pem" 2>/dev/null
fi
echo -e "${GREEN}✓ Post-update fixes applied${NC}"
echo

echo -e "${BOLD}9. Verifying update...${NC}"
# Wait a bit for containers to initialize
sleep 10

# Check if containers are running
if docker ps | grep -q amrs-maintenance-tracker; then
    echo -e "${GREEN}✓ App container is running${NC}"
    
    # Check API health
    if curl -s http://localhost:9000/api/health | grep -q "status"; then
        echo -e "${GREEN}✓ API is responding correctly${NC}"
    else
        echo -e "${YELLOW}! API is not responding yet${NC}"
        echo "This could be normal if the application is still initializing."
        echo "Check the logs with: docker logs amrs-maintenance-tracker"
    fi
else
    echo -e "${RED}✗ App container is not running${NC}"
    echo "Please check the logs: docker logs amrs-maintenance-tracker"
fi

echo
echo -e "${GREEN}${BOLD}AMRS Update Complete!${NC}"
echo "The application has been updated to the latest version."
echo
echo "If you encounter any issues, you can restore from the backup:"
echo "./restore_config.sh $BACKUP_FILE $DATA_DIR"
echo
echo "To check for any errors, view the container logs:"
echo "docker logs amrs-maintenance-tracker"
echo
echo "Access your updated AMRS system at the usual URL"
