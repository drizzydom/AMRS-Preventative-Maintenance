#!/bin/bash
# =============================================================================
# AMRS All Issues Fix Script
# This script applies fixes for all common issues in one go
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Comprehensive Fix Script${NC}"
echo "============================"
echo

# Get script directory 
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

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

# First, create a complete backup
echo -e "${BOLD}1. Creating backup of current state...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$DATA_DIR/backup"
mkdir -p "$BACKUP_DIR"

# Backup database
if [ -f "$DATA_DIR/data/app.db" ]; then
    cp "$DATA_DIR/data/app.db" "$BACKUP_DIR/app.db.$TIMESTAMP"
    echo -e "${GREEN}✓ Database backed up${NC}"
elif [ -f "$DATA_DIR/app.db" ]; then
    cp "$DATA_DIR/app.db" "$BACKUP_DIR/app.db.$TIMESTAMP"
    echo -e "${GREEN}✓ Database backed up from alternate location${NC}"
else
    echo -e "${YELLOW}! No database found to backup${NC}"
fi

# Backup docker-compose file
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    cp "$PROJECT_DIR/docker-compose.yml" "$PROJECT_DIR/docker-compose.yml.$TIMESTAMP"
    echo -e "${GREEN}✓ Docker-compose configuration backed up${NC}"
fi

echo -e "${BOLD}2. Stopping containers to apply fixes...${NC}"
cd "$PROJECT_DIR" && docker-compose down
echo -e "${GREEN}✓ Containers stopped${NC}"

echo -e "${BOLD}3. Fixing database permissions...${NC}"
# Run the database fix script
if [ -f "$SCRIPT_DIR/database_fix.sh" ]; then
    bash "$SCRIPT_DIR/database_fix.sh" "$DATA_DIR"
else
    echo -e "${YELLOW}! database_fix.sh not found, creating directories manually${NC}"
    mkdir -p "$DATA_DIR/data"
    chmod -R 777 "$DATA_DIR"
    chmod -R 777 "$DATA_DIR/data"
fi

echo -e "${BOLD}4. Fixing template permissions...${NC}"
# Run the template fix script
if [ -f "$SCRIPT_DIR/fix_template_permissions.sh" ]; then
    bash "$SCRIPT_DIR/fix_template_permissions.sh" "$DATA_DIR"
else
    echo -e "${YELLOW}! fix_template_permissions.sh not found, fixing manually${NC}"
    mkdir -p "$DATA_DIR/templates"
    chmod -R 777 "$DATA_DIR/templates"
    mkdir -p "$DATA_DIR/static"
    chmod -R 777 "$DATA_DIR/static"
fi

echo -e "${BOLD}5. Fixing network issues...${NC}"
# Run the network fix script
if [ -f "$SCRIPT_DIR/fix_networking.sh" ]; then
    bash "$SCRIPT_DIR/fix_networking.sh" "$DATA_DIR"
else
    echo -e "${YELLOW}! fix_networking.sh not found, fixing Docker network manually${NC}"
    
    # Create amrs-network if it doesn't exist
    if ! docker network ls | grep -q amrs-network; then
        docker network create amrs-network
        echo -e "${GREEN}✓ Created Docker network: amrs-network${NC}"
    fi
    
    # Update docker-compose.yml
    if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
        # Add network configuration if not present
        if ! grep -q "networks:" "$PROJECT_DIR/docker-compose.yml"; then
            cat >> "$PROJECT_DIR/docker-compose.yml" << EOF

networks:
  amrs-network:
    name: amrs-network
EOF
            echo -e "${GREEN}✓ Added network configuration to docker-compose.yml${NC}"
        fi
        
        # Make sure containers use the network
        if ! grep -q "networks:" "$PROJECT_DIR/docker-compose.yml" | grep -A5 "app:"; then
            sed -i'.tmp' '/container_name: amrs-maintenance-tracker/a\    networks:\n      - amrs-network' "$PROJECT_DIR/docker-compose.yml" 2>/dev/null || sed -i '/container_name: amrs-maintenance-tracker/a\    networks:\n      - amrs-network' "$PROJECT_DIR/docker-compose.yml" 
            sed -i'.tmp' '/container_name: amrs-nginx/a\    networks:\n      - amrs-network' "$PROJECT_DIR/docker-compose.yml" 2>/dev/null || sed -i '/container_name: amrs-nginx/a\    networks:\n      - amrs-network' "$PROJECT_DIR/docker-compose.yml"
            echo -e "${GREEN}✓ Added network configuration to services${NC}"
        fi
    fi
fi

echo -e "${BOLD}6. Creating minimal config files if needed...${NC}"
# Create minimal NGINX config if not exists
NGINX_CONF="$DATA_DIR/nginx/conf.d/default.conf"
if [ ! -f "$NGINX_CONF" ]; then
    mkdir -p $(dirname "$NGINX_CONF")
    cat > "$NGINX_CONF" << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://app:9000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        
        # Extended timeouts for slow application startup
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Health check endpoint
    location = /api/health {
        proxy_pass http://app:9000/api/health;
        proxy_set_header Host \$host;
    }
}
EOF
    echo -e "${GREEN}✓ Created minimal NGINX configuration${NC}"
fi

# Create minimal files for templates if none exist
if [ ! -f "$DATA_DIR/templates/base.html" ]; then
    mkdir -p "$DATA_DIR/templates"
    echo "<html><body><h1>AMRS Maintenance Tracker</h1><p>This is a placeholder template.</p></body></html>" > "$DATA_DIR/templates/base.html"
    echo -e "${GREEN}✓ Created minimal template file${NC}"
fi

echo -e "${BOLD}7. Starting containers with fixes applied...${NC}"
# Update Docker-Compose to run as root temporarily for debugging
sed -i'.tmp' 's/user: "1000:1000"/user: "root"/' "$PROJECT_DIR/docker-compose.yml" 2>/dev/null || sed -i 's/user: "1000:1000"/user: "root"/' "$PROJECT_DIR/docker-compose.yml" || echo "User setting not found in docker-compose.yml"

# Restart containers
cd "$PROJECT_DIR" && docker-compose up -d
echo -e "${GREEN}✓ Containers started${NC}"

# Wait for containers to initialize
echo "Waiting for containers to initialize..."
sleep 10

echo -e "${BOLD}8. Testing if fixes were successful...${NC}"
# Check container status
if docker ps | grep -q amrs-maintenance-tracker && docker ps | grep -q amrs-nginx; then
    echo -e "${GREEN}✓ Both containers are running${NC}"
else
    echo -e "${RED}✗ One or more containers failed to start${NC}"
    docker ps
fi

# Test API connection
echo "Testing API health endpoint..."
if curl -s http://localhost:9000/api/health | grep -q "status"; then
    echo -e "${GREEN}✓ API is responding correctly${NC}"
    curl -s http://localhost:9000/api/health
else
    echo -e "${RED}✗ API is not responding${NC}"
    echo "Check container logs for more details:"
    docker logs amrs-maintenance-tracker --tail 20
fi

# Test NGINX connection
echo "Testing NGINX proxy..."
if curl -s http://localhost:8080/api/health | grep -q "status"; then
    echo -e "${GREEN}✓ NGINX proxy is working correctly${NC}"
else
    echo -e "${RED}✗ NGINX proxy is not working${NC}"
    echo "Check NGINX logs:"
    docker logs amrs-nginx --tail 20
fi

echo
echo -e "${GREEN}${BOLD}All fixes have been applied!${NC}"
echo "The system should now be operational. If you continue to experience issues:"
echo "1. Check specific container logs: docker logs amrs-maintenance-tracker"
echo "2. Try running each fix script individually for more detailed output"
echo "3. Consider rebuilding the containers from scratch: docker-compose up -d --build"
echo
echo "IMPORTANT: For security, once everything is working, consider changing"
echo "back to a non-root user in docker-compose.yml:"
echo "user: \"1000:1000\""
