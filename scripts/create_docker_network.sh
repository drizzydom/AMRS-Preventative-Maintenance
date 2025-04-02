#!/bin/bash
# =============================================================================
# AMRS Docker Network Setup Script
# This script sets up a dedicated Docker network for AMRS containers
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Docker Network Setup${NC}"
echo "========================="
echo

# Get network name or generate a unique one
if [ -n "$1" ]; then
    NETWORK_NAME="$1"
    echo "Using provided network name: $NETWORK_NAME"
else
    # Use a fixed network name rather than timestamp-based to prevent proliferation
    NETWORK_NAME="amrs_network"
    echo "Using fixed network name: $NETWORK_NAME"
fi

echo -e "${BOLD}1. Checking for existing Docker networks...${NC}"
EXISTING_NETWORKS=$(docker network ls --filter name="$NETWORK_NAME" --format "{{.Name}}")

# Nuclear approach to network cleanup - remove any existing network with this name
if [[ -n "$EXISTING_NETWORKS" ]]; then
    echo -e "${YELLOW}! Network '$NETWORK_NAME' already exists - removing it${NC}"
    
    # First disconnect any connected containers
    CONNECTED_CONTAINERS=$(docker network inspect "$NETWORK_NAME" -f '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
    if [[ -n "$CONNECTED_CONTAINERS" ]]; then
        echo "Disconnecting containers from network: $CONNECTED_CONTAINERS"
        for container in $CONNECTED_CONTAINERS; do
            docker network disconnect -f "$NETWORK_NAME" "$container" 2>/dev/null || true
        done
    fi
    
    # Now remove the network
    docker network rm "$NETWORK_NAME" 2>/dev/null || true
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Removed existing network${NC}"
    else
        echo -e "${RED}✗ Failed to remove network${NC}"
        echo "Nuclear option: Pruning all unused networks..."
        docker network prune -f
    fi
fi

echo -e "${BOLD}2. Creating new Docker network...${NC}"
# First try with default driver
if docker network create "$NETWORK_NAME" 2>/dev/null; then
    echo -e "${GREEN}✓ Created network '$NETWORK_NAME'${NC}"
else
    echo -e "${YELLOW}! First attempt failed, trying with bridge driver...${NC}"
    
    # Try with explicit bridge driver
    if docker network create --driver bridge "$NETWORK_NAME" 2>/dev/null; then
        echo -e "${GREEN}✓ Created network '$NETWORK_NAME' with bridge driver${NC}"
    else
        echo -e "${RED}✗ Failed to create network with bridge driver${NC}"
        
        # Try with subnet specification as last resort
        echo -e "${YELLOW}! Trying with subnet specification...${NC}"
        if docker network create --driver bridge --subnet=172.20.0.0/16 "$NETWORK_NAME" 2>/dev/null; then
            echo -e "${GREEN}✓ Created network '$NETWORK_NAME' with custom subnet${NC}"
        else
            echo -e "${RED}✗ All attempts to create network failed${NC}"
            echo "Using default 'bridge' network instead."
            NETWORK_NAME="bridge"
        fi
    fi
fi

echo -e "${BOLD}3. Verifying network configuration...${NC}"
docker network inspect "$NETWORK_NAME" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    # Get network details
    SUBNET=$(docker network inspect "$NETWORK_NAME" -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
    GATEWAY=$(docker network inspect "$NETWORK_NAME" -f '{{range .IPAM.Config}}{{.Gateway}}{{end}}')
    DRIVER=$(docker network inspect "$NETWORK_NAME" -f '{{.Driver}}')
    
    echo -e "${GREEN}✓ Network '$NETWORK_NAME' is ready${NC}"
    echo "   Driver: $DRIVER"
    echo "   Subnet: $SUBNET"
    echo "   Gateway: $GATEWAY"
else
    echo -e "${RED}✗ Unable to verify network${NC}"
    exit 1
fi

# Output network name for use by other scripts
echo "$NETWORK_NAME" > /tmp/amrs_network_name

echo
echo -e "${GREEN}${BOLD}Docker network setup complete!${NC}"
echo "Created Docker network: $NETWORK_NAME"
echo "This network will be used for communication between AMRS containers."
