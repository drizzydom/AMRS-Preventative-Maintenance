#!/bin/bash
# =============================================================================
# AMRS Container Network Fix Script
# This script fixes network connectivity issues between Docker containers
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Container Network Fix Script${NC}"
echo "==============================="
echo

# Define container names
APP_CONTAINER="amrs-maintenance-tracker"
NGINX_CONTAINER="amrs-nginx"

echo -e "${BOLD}1. Checking if containers are running...${NC}"
APP_RUNNING=false
NGINX_RUNNING=false

if docker ps | grep -q $APP_CONTAINER; then
    echo -e "${GREEN}✓ App container is running${NC}"
    APP_RUNNING=true
else
    echo -e "${RED}✗ App container is not running${NC}"
fi

if docker ps | grep -q $NGINX_CONTAINER; then
    echo -e "${GREEN}✓ Nginx container is running${NC}"
    NGINX_RUNNING=true
else
    echo -e "${RED}✗ Nginx container is not running${NC}"
fi

if [ "$APP_RUNNING" = false ] || [ "$NGINX_RUNNING" = false ]; then
    echo "Starting containers..."
    docker-compose up -d
    sleep 5
    
    # Check again
    if docker ps | grep -q $APP_CONTAINER; then
        echo -e "${GREEN}✓ App container is now running${NC}"
        APP_RUNNING=true
    else
        echo -e "${RED}✗ App container still not running${NC}"
    fi
    
    if docker ps | grep -q $NGINX_CONTAINER; then
        echo -e "${GREEN}✓ Nginx container is now running${NC}"
        NGINX_RUNNING=true
    else
        echo -e "${RED}✗ Nginx container still not running${NC}"
    fi
    
    if [ "$APP_RUNNING" = false ] || [ "$NGINX_RUNNING" = false ]; then
        echo -e "${RED}✗ Cannot proceed without both containers running${NC}"
        exit 1
    fi
fi
echo

echo -e "${BOLD}2. Checking current network setup...${NC}"
APP_NETWORK=$(docker inspect -f '{{range $key, $val := .NetworkSettings.Networks}}{{$key}}{{end}}' $APP_CONTAINER)
NGINX_NETWORK=$(docker inspect -f '{{range $key, $val := .NetworkSettings.Networks}}{{$key}}{{end}}' $NGINX_CONTAINER)

echo "App container network: $APP_NETWORK"
echo "Nginx container network: $NGINX_NETWORK"

if [ "$APP_NETWORK" != "$NGINX_NETWORK" ]; then
    echo -e "${RED}✗ Containers are on different networks!${NC}"
    NETWORK_MISMATCH=true
else
    echo -e "${GREEN}✓ Containers are on the same network${NC}"
    NETWORK_MISMATCH=false
fi

echo -e "${BOLD}3. Checking hostname resolution...${NC}"
echo "From $APP_CONTAINER to $NGINX_CONTAINER:"
APP_CAN_RESOLVE=$(docker exec $APP_CONTAINER getent hosts nginx 2>/dev/null || echo "Failed")
if [ "$APP_CAN_RESOLVE" != "Failed" ]; then
    echo -e "${GREEN}✓ App container can resolve 'nginx' hostname:${NC}"
    echo "$APP_CAN_RESOLVE"
else
    echo -e "${RED}✗ App container cannot resolve 'nginx' hostname${NC}"
    APP_RESOLVE_ISSUE=true
fi

echo "From $NGINX_CONTAINER to $APP_CONTAINER:"
NGINX_CAN_RESOLVE=$(docker exec $NGINX_CONTAINER getent hosts app 2>/dev/null || docker exec $NGINX_CONTAINER getent hosts $APP_CONTAINER 2>/dev/null || echo "Failed")
if [ "$NGINX_CAN_RESOLVE" != "Failed" ]; then
    echo -e "${GREEN}✓ Nginx container can resolve 'app' hostname:${NC}"
    echo "$NGINX_CAN_RESOLVE"
else
    echo -e "${RED}✗ Nginx container cannot resolve 'app' hostname${NC}"
    NGINX_RESOLVE_ISSUE=true
fi
echo

echo -e "${BOLD}4. Testing connectivity between containers...${NC}"
echo "From $APP_CONTAINER to $NGINX_CONTAINER:"
APP_CAN_PING=$(docker exec $APP_CONTAINER ping -c 1 nginx 2>/dev/null || docker exec $APP_CONTAINER ping -c 1 $NGINX_CONTAINER 2>/dev/null || echo "Failed")
if [ "$APP_CAN_PING" != "Failed" ]; then
    echo -e "${GREEN}✓ App container can ping Nginx container${NC}"
else
    echo -e "${RED}✗ App container cannot ping Nginx container${NC}"
    APP_PING_ISSUE=true
fi

echo "From $NGINX_CONTAINER to $APP_CONTAINER:"
NGINX_CAN_PING=$(docker exec $NGINX_CONTAINER ping -c 1 app 2>/dev/null || docker exec $NGINX_CONTAINER ping -c 1 $APP_CONTAINER 2>/dev/null || echo "Failed")
if [ "$NGINX_CAN_PING" != "Failed" ]; then
    echo -e "${GREEN}✓ Nginx container can ping App container${NC}"
else
    echo -e "${RED}✗ Nginx container cannot ping App container${NC}"
    NGINX_PING_ISSUE=true
fi
echo

echo -e "${BOLD}5. Applying network fixes...${NC}"

# Fix 1: Create hosts file entries
echo "Adding hostname mappings to /etc/hosts files..."

# Get IP addresses
APP_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $APP_CONTAINER)
NGINX_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $NGINX_CONTAINER)

echo "App container IP: $APP_IP"
echo "Nginx container IP: $NGINX_IP"

# Add entries to app container hosts file
docker exec $APP_CONTAINER bash -c "echo '$NGINX_IP nginx $NGINX_CONTAINER' >> /etc/hosts"
docker exec $APP_CONTAINER bash -c "echo '127.0.0.1 app $APP_CONTAINER' >> /etc/hosts"
echo -e "${GREEN}✓ Added hostname entries to app container${NC}"

# Add entries to nginx container hosts file
docker exec $NGINX_CONTAINER bash -c "echo '$APP_IP app $APP_CONTAINER' >> /etc/hosts"
docker exec $NGINX_CONTAINER bash -c "echo '127.0.0.1 nginx $NGINX_CONTAINER' >> /etc/hosts"
echo -e "${GREEN}✓ Added hostname entries to nginx container${NC}"

# Fix 2: Network match fix (if needed)
if [ "$NETWORK_MISMATCH" = true ]; then
    echo "Creating a common network and reconnecting containers..."
    
    # Create a new common network if it doesn't exist
    COMMON_NETWORK="amrs_network"
    if ! docker network ls | grep -q "$COMMON_NETWORK"; then
        docker network create "$COMMON_NETWORK"
        echo -e "${GREEN}✓ Created new network: $COMMON_NETWORK${NC}"
    fi
    
    # Connect both containers to the common network
    docker network connect "$COMMON_NETWORK" $APP_CONTAINER 2>/dev/null || true
    docker network connect "$COMMON_NETWORK" $NGINX_CONTAINER 2>/dev/null || true
    echo -e "${GREEN}✓ Connected containers to common network${NC}"
    
    # Update docker-compose.yml
    DOCKER_COMPOSE_FILE="docker-compose.yml"
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        # Backup the original
        cp "$DOCKER_COMPOSE_FILE" "${DOCKER_COMPOSE_FILE}.bak.$(date +%s)"
        
        # Add network configuration
        if ! grep -q "networks:" "$DOCKER_COMPOSE_FILE"; then
            echo "
networks:
  default:
    name: $COMMON_NETWORK
    external: true" >> "$DOCKER_COMPOSE_FILE"
            echo -e "${GREEN}✓ Added network configuration to docker-compose.yml${NC}"
        fi
    fi
fi

# Fix 3: Update nginx configuration
echo "Updating Nginx configuration..."
NGINX_CONF_DIR="/volume1/docker/amrs-data/nginx/conf.d"
if [ ! -d "$NGINX_CONF_DIR" ]; then
    NGINX_CONF_DIR="$HOME/amrs-data/nginx/conf.d"
fi

if [ -d "$NGINX_CONF_DIR" ]; then
    NGINX_CONF="$NGINX_CONF_DIR/default.conf"
    
    # Backup the original
    cp "$NGINX_CONF" "${NGINX_CONF}.bak" 2>/dev/null || true
    
    # Update proxy_pass to use IP address directly if needed
    if [ "$NGINX_RESOLVE_ISSUE" = true ]; then
        sed -i.bak "s|proxy_pass http://app:9000;|proxy_pass http://$APP_IP:9000;|g" "$NGINX_CONF" 2>/dev/null || 
        sed -i "s|proxy_pass http://app:9000;|proxy_pass http://$APP_IP:9000;|g" "$NGINX_CONF" 2>/dev/null
        
        echo -e "${GREEN}✓ Updated Nginx configuration to use direct IP address${NC}"
        
        # Restart nginx
        docker restart $NGINX_CONTAINER
        echo -e "${GREEN}✓ Restarted Nginx container${NC}"
    fi
else
    echo -e "${YELLOW}! Nginx configuration directory not found${NC}"
fi
echo

echo -e "${BOLD}6. Setting up container aliases...${NC}"
# Create alias scripts to help with naming
docker exec $APP_CONTAINER bash -c "echo 'alias app=\"hostname\"' >> /etc/bash.bashrc"
docker exec $APP_CONTAINER bash -c "echo 'alias nginx=\"ping -c 1 nginx\"' >> /etc/bash.bashrc"
docker exec $NGINX_CONTAINER bash -c "echo 'alias nginx=\"hostname\"' >> /etc/bash.bashrc"
docker exec $NGINX_CONTAINER bash -c "echo 'alias app=\"ping -c 1 app\"' >> /etc/bash.bashrc"
echo -e "${GREEN}✓ Container aliases configured${NC}"
echo

echo -e "${BOLD}7. Testing fixes...${NC}"
echo "Testing resolution from app to nginx:"
docker exec $APP_CONTAINER getent hosts nginx || echo "Still can't resolve"
echo "Testing ping from app to nginx:"
docker exec $APP_CONTAINER ping -c 1 nginx 2>/dev/null && echo -e "${GREEN}✓ App can ping Nginx${NC}" || echo -e "${RED}✗ App still can't ping Nginx${NC}"

echo "Testing resolution from nginx to app:"
docker exec $NGINX_CONTAINER getent hosts app || echo "Still can't resolve"
echo "Testing ping from nginx to app:"
docker exec $NGINX_CONTAINER ping -c 1 app 2>/dev/null && echo -e "${GREEN}✓ Nginx can ping App${NC}" || echo -e "${RED}✗ Nginx still can't ping App${NC}"
echo

# Test if nginx can connect to app's port 9000
echo "Testing if Nginx can connect to App's port 9000..."
if docker exec $NGINX_CONTAINER bash -c "nc -z -v app 9000 2>&1" | grep -q "open"; then
    echo -e "${GREEN}✓ Nginx can connect to App's port 9000${NC}"
else
    echo -e "${RED}✗ Nginx cannot connect to App's port 9000${NC}"
    # Try direct IP
    if docker exec $NGINX_CONTAINER bash -c "nc -z -v $APP_IP 9000 2>&1" | grep -q "open"; then
        echo -e "${GREEN}✓ Nginx can connect to App's port 9000 using direct IP${NC}"
    else
        echo -e "${RED}✗ Nginx cannot connect to App's port 9000 even with direct IP${NC}"
    fi
fi

echo -e "${GREEN}${BOLD}Network fix completed!${NC}"
echo "The containers should now be able to communicate properly."
echo "If issues persist:"
echo "1. Try creating a specific docker-compose override file"
echo "2. Verify port 9000 is open and Flask is binding to 0.0.0.0 not localhost"
echo "3. Run the nuclear network fix: ./scripts/nuclear_network_fix.sh"
