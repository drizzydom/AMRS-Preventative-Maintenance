#!/bin/bash
# =============================================================================
# AMRS Connection Test Script
# This script performs basic connection tests without complex checks
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Connection Test${NC}"
echo "==================="
echo

# Get ports from arguments or use defaults
APP_PORT=${1:-9000}
HTTP_PORT=${2:-8080}
HTTPS_PORT=${3:-8443}

# Check Flask API connection
echo -e "${BOLD}Testing Flask API connection (http://localhost:$APP_PORT/api/health)...${NC}"
if curl -s http://localhost:$APP_PORT/api/health | grep -q "status"; then
    echo -e "${GREEN}✓ Flask API is responding${NC}"
    curl -s http://localhost:$APP_PORT/api/health | jq . 2>/dev/null || echo "Response: $(curl -s http://localhost:$APP_PORT/api/health)"
else
    echo -e "${RED}✗ Cannot connect to Flask API${NC}"
    echo "Trying with curl verbose mode:"
    curl -v http://localhost:$APP_PORT/api/health 2>&1 | grep -E "Failed to connect|Connection refused|timed out"
fi
echo

# Check Nginx HTTP connection
echo -e "${BOLD}Testing Nginx HTTP connection (http://localhost:$HTTP_PORT/api/health)...${NC}"
if curl -s http://localhost:$HTTP_PORT/api/health | grep -q "status"; then
    echo -e "${GREEN}✓ Nginx HTTP is responding${NC}"
    curl -s http://localhost:$HTTP_PORT/api/health | jq . 2>/dev/null || echo "Response: $(curl -s http://localhost:$HTTP_PORT/api/health)"
else
    echo -e "${RED}✗ Cannot connect to Nginx HTTP${NC}"
    echo "Trying with curl verbose mode:"
    curl -v http://localhost:$HTTP_PORT/api/health 2>&1 | grep -E "Failed to connect|Connection refused|timed out"
fi
echo

# Check Nginx HTTPS connection
echo -e "${BOLD}Testing Nginx HTTPS connection (https://localhost:$HTTPS_PORT/api/health)...${NC}"
if curl -k -s https://localhost:$HTTPS_PORT/api/health | grep -q "status"; then
    echo -e "${GREEN}✓ Nginx HTTPS is responding${NC}"
    curl -k -s https://localhost:$HTTPS_PORT/api/health | jq . 2>/dev/null || echo "Response: $(curl -k -s https://localhost:$HTTPS_PORT/api/health)"
else
    echo -e "${RED}✗ Cannot connect to Nginx HTTPS${NC}"
    echo "Trying with curl verbose mode:"
    curl -k -v https://localhost:$HTTPS_PORT/api/health 2>&1 | grep -E "Failed to connect|Connection refused|timed out"
fi
echo

# Check for listening ports on host
echo -e "${BOLD}Checking for listening ports on host...${NC}"
if command -v netstat &>/dev/null; then
    echo "Netstat results:"
    netstat -tuln | grep -E "$APP_PORT|$HTTP_PORT|$HTTPS_PORT"
elif command -v ss &>/dev/null; then
    echo "SS results:"
    ss -tuln | grep -E "$APP_PORT|$HTTP_PORT|$HTTPS_PORT"
else
    echo -e "${YELLOW}! Could not find netstat or ss to check ports${NC}"
fi
echo

# Check Docker port mappings
echo -e "${BOLD}Checking Docker port mappings...${NC}"
echo "App container ports:"
docker port amrs-maintenance-tracker 2>/dev/null || echo "No port mappings found"

echo "Nginx container ports:"
docker port amrs-nginx 2>/dev/null || echo "No port mappings found"
echo

echo -e "${BOLD}Checking internal container networking...${NC}"
echo "Trying to connect from app container to nginx container:"
docker exec amrs-maintenance-tracker ping -c 1 amrs-nginx 2>/dev/null \
    && echo -e "${GREEN}✓ App can reach Nginx${NC}" \
    || echo -e "${RED}✗ App cannot reach Nginx${NC}"

echo "Trying connection to Flask from Nginx container:"
docker exec amrs-nginx curl -s http://amrs-maintenance-tracker:9000/api/health 2>/dev/null \
    && echo -e "${GREEN}✓ Nginx can reach Flask API${NC}" \
    || echo -e "${RED}✗ Nginx cannot reach Flask API${NC}"

echo
echo -e "${BOLD}Connection test complete!${NC}"
echo "For more detailed diagnostics, run: ./scripts/health_check.sh"
