#!/bin/bash
# =============================================================================
# AMRS Quick Diagnostics Script
# This script performs quick diagnostics on the AMRS system
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Quick Diagnostics${NC}"
echo "======================"
echo

# Check if Docker is running
echo -e "${BOLD}1. Checking Docker service...${NC}"
if docker info &>/dev/null; then
    echo -e "${GREEN}✓ Docker is running${NC}"
else
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "Try starting Docker with: sudo systemctl start docker"
    echo "Or on Synology, start Docker from the package center"
    exit 1
fi
echo

# Check if AMRS containers are running
echo -e "${BOLD}2. Checking AMRS containers...${NC}"
if docker ps | grep -q amrs-maintenance-tracker; then
    echo -e "${GREEN}✓ App container is running${NC}"
else
    echo -e "${RED}✗ App container is not running${NC}"
fi

if docker ps | grep -q amrs-nginx; then
    echo -e "${GREEN}✓ Nginx container is running${NC}"
else
    echo -e "${RED}✗ Nginx container is not running${NC}"
fi
echo

# Quick check of the API
echo -e "${BOLD}3. Testing API connection...${NC}"
if curl -s http://localhost:9000/api/health >/dev/null; then
    echo -e "${GREEN}✓ API is responding${NC}"
    API_RESPONSE=$(curl -s http://localhost:9000/api/health | grep -o '"status":"[^"]*"')
    echo "   Status: $API_RESPONSE"
else
    echo -e "${RED}✗ API is not responding${NC}"
fi
echo

# Check network connectivity between containers
echo -e "${BOLD}4. Checking inter-container connectivity...${NC}"
if docker exec amrs-maintenance-tracker ping -c 1 amrs-nginx >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Containers can reach each other${NC}"
else
    echo -e "${RED}✗ Containers cannot reach each other${NC}"
    echo "   This may indicate a Docker networking issue"
fi
echo

# Check disk space
echo -e "${BOLD}5. Checking disk space...${NC}"
if df -h / | awk 'NR==2 {print $5}' | grep -q "9[0-9]%\|100%"; then
    echo -e "${RED}✗ Disk space is critically low!${NC}"
    df -h /
else
    echo -e "${GREEN}✓ Disk space is adequate${NC}"
    df -h / | grep -Eo "[0-9]+%"
fi
echo

# Check recent logs for errors
echo -e "${BOLD}6. Checking recent logs for errors...${NC}"
if docker logs --since=1h amrs-maintenance-tracker 2>&1 | grep -i "error\|exception\|failed" | grep -v "DEBUG" >/dev/null; then
    echo -e "${YELLOW}! Found errors in recent logs${NC}"
    docker logs --since=1h amrs-maintenance-tracker 2>&1 | grep -i "error\|exception\|failed" | grep -v "DEBUG" | head -5
else
    echo -e "${GREEN}✓ No obvious errors in recent logs${NC}"
fi
echo

echo -e "${BOLD}Diagnostics Complete!${NC}"
echo "For more detailed health checks, run:"
echo "./scripts/health_check.sh"
