#!/bin/bash
# =============================================================================
# AMRS Prerequisites Check Script
# This script verifies that all required software is installed and running
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Prerequisites Check${NC}"
echo "========================="
echo

PREREQUISITES_OK=true

# Check Docker installation
echo -e "${BOLD}1. Checking for Docker...${NC}"
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo -e "${GREEN}✓ Docker is installed${NC}"
    echo "   $docker_version"
else
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "   Please install Docker through Synology Package Center"
    PREREQUISITES_OK=false
fi
echo

# Check Docker Compose installation
echo -e "${BOLD}2. Checking for Docker Compose...${NC}"
if command -v docker-compose &> /dev/null; then
    compose_version=$(docker-compose --version)
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"
    echo "   $compose_version"
else
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "   Please install Docker Compose through Synology Package Center"
    PREREQUISITES_OK=false
fi
echo

# Check if Docker daemon is running
echo -e "${BOLD}3. Checking Docker daemon status...${NC}"
if docker info &> /dev/null; then
    echo -e "${GREEN}✓ Docker daemon is running${NC}"
else
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    echo "   Please start Docker from Synology Docker app"
    PREREQUISITES_OK=false
fi
echo

# Check if we're running on a Synology device
echo -e "${BOLD}4. Checking for Synology...${NC}"
if [ -f "/etc/synoinfo.conf" ]; then
    echo -e "${GREEN}✓ Running on a Synology device${NC}"
    
    # Get DSM version
    DSM_VERSION=$(grep "^majorversion" /etc/synoinfo.conf | cut -d'"' -f2).$(grep "^minorversion" /etc/synoinfo.conf | cut -d'"' -f2)
    echo "   DSM Version: $DSM_VERSION"
else
    echo -e "${YELLOW}! Not running on a Synology device${NC}"
    echo "   Some paths and configurations might need adjustments"
fi
echo

# Check available disk space
echo -e "${BOLD}5. Checking available disk space...${NC}"
if command -v df &> /dev/null; then
    SPACE_INFO=$(df -h /volume1 | grep -v Filesystem)
    AVAILABLE=$(echo "$SPACE_INFO" | awk '{print $4}')
    USAGE_PCT=$(echo "$SPACE_INFO" | awk '{print $5}')
    echo "   Available space: $AVAILABLE ($USAGE_PCT used)"
    
    # Extract numeric percentage
    USAGE_NUM=$(echo "$USAGE_PCT" | sed 's/%//')
    if [ "$USAGE_NUM" -gt 90 ]; then
        echo -e "${YELLOW}! Disk space is running low${NC}"
        echo "   Consider cleaning up some files before installation"
    else
        echo -e "${GREEN}✓ Sufficient disk space available${NC}"
    fi
else
    echo -e "${YELLOW}! Could not determine available disk space${NC}"
fi
echo

# Check system memory
echo -e "${BOLD}6. Checking system memory...${NC}"
if command -v free &> /dev/null; then
    MEM_TOTAL=$(free -h | grep Mem | awk '{print $2}')
    MEM_AVAILABLE=$(free -h | grep Mem | awk '{print $7}')
    echo "   Total memory: $MEM_TOTAL"
    echo "   Available memory: $MEM_AVAILABLE"
else
    # Alternative for Synology which might not have free command
    if [ -f "/proc/meminfo" ]; then
        MEM_TOTAL=$(grep MemTotal /proc/meminfo | awk '{print $2 / 1024 / 1024}' | xargs printf "%.1f GB")
        MEM_FREE=$(grep MemAvailable /proc/meminfo | awk '{print $2 / 1024 / 1024}' | xargs printf "%.1f GB")
        echo "   Total memory: $MEM_TOTAL"
        echo "   Available memory: $MEM_FREE"
    else
        echo -e "${YELLOW}! Could not determine system memory${NC}"
    fi
fi
echo

# Final status
if [ "$PREREQUISITES_OK" = true ]; then
    echo -e "${GREEN}${BOLD}All prerequisites satisfied!${NC}"
    echo "You can proceed with the installation."
    exit 0
else
    echo -e "${RED}${BOLD}Some prerequisites are missing!${NC}"
    echo "Please install the required components before proceeding."
    exit 1
fi
