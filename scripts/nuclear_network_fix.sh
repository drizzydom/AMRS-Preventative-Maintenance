#!/bin/bash
# =============================================================================
# AMRS Docker Network Nuclear Fix
# This script forcibly removes and recreates Docker networks for AMRS
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Docker Network Nuclear Fix${NC}"
echo "=============================="
echo

# Get network name from argument
NETWORK_NAME=${1:-"amrs_network"}
echo "Working with network name: $NETWORK_NAME"

echo -e "${BOLD}1. Stopping all related containers...${NC}"
docker-compose down --remove-orphans 2>/dev/null || true
docker ps | grep -E 'amrs|nginx' | awk '{print $1}' | xargs -r docker stop

echo -e "${BOLD}2. Disconnecting ALL containers from the network...${NC}"
# Find all containers connected to the network and disconnect them
CONNECTED_CONTAINERS=$(docker network inspect $NETWORK_NAME -f '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
for container in $CONNECTED_CONTAINERS; do
    echo "Disconnecting container: $container"
    docker network disconnect -f $NETWORK_NAME $container 2>/dev/null || true
done
echo -e "${GREEN}✓ All containers disconnected from network${NC}"

echo -e "${BOLD}3. Removing the network...${NC}"
# Remove the network
docker network rm $NETWORK_NAME 2>/dev/null || true
echo -e "${GREEN}✓ Network removed (if it existed)${NC}"

echo -e "${BOLD}4. Pruning all Docker networks...${NC}"
# Prune all unused networks to clean up
docker network prune -f
echo -e "${GREEN}✓ All unused networks pruned${NC}"

echo -e "${BOLD}5. Creating a fresh network...${NC}"
# Create a new clean network
if docker network create $NETWORK_NAME; then
    echo -e "${GREEN}✓ Created fresh network: $NETWORK_NAME${NC}"
else
    echo -e "${RED}✗ Failed to create network${NC}"
    echo "Trying with explicit bridge driver..."
    
    if docker network create --driver bridge $NETWORK_NAME; then
        echo -e "${GREEN}✓ Created fresh network with bridge driver: $NETWORK_NAME${NC}"
    else
        echo -e "${RED}✗ Still failed. Last attempt with custom subnet...${NC}"
        
        if docker network create --driver bridge --subnet=172.30.0.0/16 $NETWORK_NAME; then
            echo -e "${GREEN}✓ Created network with custom subnet: $NETWORK_NAME${NC}"
        else
            echo -e "${RED}✗ All attempts failed. Using default 'bridge' network${NC}"
            NETWORK_NAME="bridge"
        fi
    fi
fi

echo -e "${BOLD}6. Updating docker-compose.yml network configuration...${NC}"
# Update docker-compose.yml file if it exists
if [ -f docker-compose.yml ]; then
    # Backup the original
    cp docker-compose.yml docker-compose.yml.bak
    
    # Remove existing networks section
    sed -i.tmp '/^networks:/,$d' docker-compose.yml 2>/dev/null || true
    
    # Add new networks section with external: true
    cat >> docker-compose.yml << EOL

networks:
  default:
    name: $NETWORK_NAME
    external: true
EOL
    echo -e "${GREEN}✓ docker-compose.yml updated${NC}"
else
    echo -e "${YELLOW}! docker-compose.yml not found${NC}"
fi

# Save network name for other scripts
echo "$NETWORK_NAME" > /tmp/amrs_network_name

echo
echo -e "${GREEN}${BOLD}Network fix completed!${NC}"
echo "Use the following network name in your docker-compose.yml:"
echo "networks:"
echo "  default:"
echo "    name: $NETWORK_NAME"
echo "    external: true"
