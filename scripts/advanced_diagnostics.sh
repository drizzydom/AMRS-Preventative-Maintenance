#!/bin/bash
# =============================================================================
# AMRS Advanced Diagnostics Script
# This script performs in-depth diagnostics and provides fixes
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Advanced Diagnostics${NC}"
echo "========================="
echo

# Get working directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Define container names
APP_CONTAINER="amrs-maintenance-tracker"
NGINX_CONTAINER="amrs-nginx"

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

echo -e "${BOLD}1. System Information${NC}"
echo -e "${BLUE}Operating System:${NC} $(uname -a)"
echo -e "${BLUE}Docker Version:${NC} $(docker --version)"
echo -e "${BLUE}Docker Compose:${NC} $(docker-compose --version 2>/dev/null || echo "Not installed")"
echo -e "${BLUE}User:${NC} $(whoami)"
echo -e "${BLUE}Current directory:${NC} $(pwd)"
echo

echo -e "${BOLD}2. Docker Container Status${NC}"
if docker ps | grep -q $APP_CONTAINER; then
    echo -e "${GREEN}✓ App container is running${NC}"
    APP_RUNNING=true
    
    # Get container details
    APP_ID=$(docker ps -q -f "name=$APP_CONTAINER")
    APP_IMAGE=$(docker inspect --format='{{.Config.Image}}' $APP_ID)
    APP_CREATED=$(docker inspect --format='{{.Created}}' $APP_ID)
    APP_IP=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $APP_ID)
    APP_PORTS=$(docker inspect --format='{{range $p, $conf := .NetworkSettings.Ports}}{{$p}} -> {{(index $conf 0).HostPort}}{{println}}{{end}}' $APP_ID)
    APP_MOUNTS=$(docker inspect --format='{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}' $APP_ID)
    
    echo -e "${BLUE}Container ID:${NC} $APP_ID"
    echo -e "${BLUE}Image:${NC} $APP_IMAGE"
    echo -e "${BLUE}Created:${NC} $APP_CREATED"
    echo -e "${BLUE}IP Address:${NC} $APP_IP"
    echo -e "${BLUE}Ports:${NC}\n$APP_PORTS"
    echo -e "${BLUE}Mounts:${NC}\n$APP_MOUNTS"
else
    echo -e "${RED}✗ App container is not running${NC}"
    APP_RUNNING=false
fi
echo

if docker ps | grep -q $NGINX_CONTAINER; then
    echo -e "${GREEN}✓ Nginx container is running${NC}"
    NGINX_RUNNING=true
    
    # Get container details
    NGINX_ID=$(docker ps -q -f "name=$NGINX_CONTAINER")
    NGINX_IMAGE=$(docker inspect --format='{{.Config.Image}}' $NGINX_ID)
    NGINX_IP=$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $NGINX_ID)
    NGINX_PORTS=$(docker inspect --format='{{range $p, $conf := .NetworkSettings.Ports}}{{$p}} -> {{(index $conf 0).HostPort}}{{println}}{{end}}' $NGINX_ID)
    
    echo -e "${BLUE}Container ID:${NC} $NGINX_ID"
    echo -e "${BLUE}Image:${NC} $NGINX_IMAGE"
    echo -e "${BLUE}IP Address:${NC} $NGINX_IP"
    echo -e "${BLUE}Ports:${NC}\n$NGINX_PORTS"
else
    echo -e "${RED}✗ Nginx container is not running${NC}"
    NGINX_RUNNING=false
fi
echo

echo -e "${BOLD}3. Network Diagnostics${NC}"
echo "Checking Docker networks..."
docker network ls | grep -E "amrs|bridge"
echo

echo "Checking container network details..."
if [ "$APP_RUNNING" = true ]; then
    APP_NETWORKS=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' $APP_CONTAINER)
    echo -e "${BLUE}App container network:${NC} $APP_NETWORKS"
    
    # Check networking inside app container
    echo "Network interfaces in app container:"
    docker exec $APP_CONTAINER ip addr show 2>/dev/null || docker exec $APP_CONTAINER ifconfig 2>/dev/null
    
    echo "DNS resolution in app container:"
    docker exec $APP_CONTAINER cat /etc/resolv.conf 2>/dev/null
    
    echo "Hosts file in app container:"
    docker exec $APP_CONTAINER cat /etc/hosts 2>/dev/null
fi
echo

if [ "$NGINX_RUNNING" = true ]; then
    NGINX_NETWORKS=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' $NGINX_CONTAINER)
    echo -e "${BLUE}Nginx container network:${NC} $NGINX_NETWORKS"
fi
echo

echo "Testing inter-container communication..."
if [ "$APP_RUNNING" = true ] && [ "$NGINX_RUNNING" = true ]; then
    echo "Testing from app -> nginx:"
    docker exec $APP_CONTAINER ping -c 1 nginx 2>/dev/null && 
        echo -e "${GREEN}✓ App can ping nginx${NC}" || 
        echo -e "${RED}✗ App cannot ping nginx${NC}"
    
    echo "Testing from nginx -> app:"
    docker exec $NGINX_CONTAINER ping -c 1 app 2>/dev/null && 
        echo -e "${GREEN}✓ Nginx can ping app${NC}" || 
        echo -e "${RED}✗ Nginx cannot ping app${NC}"
    
    echo "Testing app port access from nginx:"
    docker exec $NGINX_CONTAINER curl -s http://app:9000/api/health >/dev/null 2>&1 && 
        echo -e "${GREEN}✓ Nginx can access app's API${NC}" || 
        echo -e "${RED}✗ Nginx cannot access app's API${NC}"
else
    echo -e "${YELLOW}! Cannot test inter-container communication${NC}"
fi
echo

echo -e "${BOLD}4. Volume and Permissions Diagnostics${NC}"
if [ "$APP_RUNNING" = true ]; then
    echo "Checking mounted directories in app container:"
    docker exec $APP_CONTAINER bash -c "ls -la /app/templates /app/static /app/data 2>/dev/null" || 
        echo "One or more directories not found"
    
    echo "Testing file creation in key directories:"
    docker exec $APP_CONTAINER bash -c "touch /app/data/test_write.tmp 2>/dev/null && echo 'Can write to /app/data' && rm /app/data/test_write.tmp" || 
        echo -e "${RED}Cannot write to /app/data${NC}"
    
    docker exec $APP_CONTAINER bash -c "touch /app/templates/test_write.tmp 2>/dev/null && echo 'Can write to /app/templates' && rm /app/templates/test_write.tmp" || 
        echo -e "${RED}Cannot write to /app/templates${NC}"
    
    docker exec $APP_CONTAINER bash -c "touch /app/static/test_write.tmp 2>/dev/null && echo 'Can write to /app/static' && rm /app/static/test_write.tmp" || 
        echo -e "${RED}Cannot write to /app/static${NC}"
    
    # Check user in container
    echo "User running in container:"
    docker exec $APP_CONTAINER id
else
    echo -e "${YELLOW}! Cannot check volumes and permissions${NC}"
fi
echo

echo -e "${BOLD}5. Application Errors Analysis${NC}"
if [ "$APP_RUNNING" = true ]; then
    echo "Checking app container logs for errors..."
    APP_ERRORS=$(docker logs $APP_CONTAINER 2>&1 | grep -i "error\|exception\|traceback" | grep -v "DEBUG" | tail -20)
    
    if [ -n "$APP_ERRORS" ]; then
        echo -e "${RED}Found errors in app logs:${NC}"
        echo "$APP_ERRORS"
        
        # Categorize errors
        if echo "$APP_ERRORS" | grep -q "Permission\|denied\|permission"; then
            PERMISSION_ERRORS=true
            echo -e "${YELLOW}! Permission-related errors detected${NC}"
        fi
        
        if echo "$APP_ERRORS" | grep -q "database\|sqlite\|db"; then
            DB_ERRORS=true
            echo -e "${YELLOW}! Database-related errors detected${NC}"
        fi
        
        if echo "$APP_ERRORS" | grep -q "No such file\|not found\|ImportError\|ModuleNotFoundError"; then
            MISSING_FILES=true
            echo -e "${YELLOW}! Missing files or modules detected${NC}"
        fi
    else
        echo -e "${GREEN}✓ No obvious errors in app logs${NC}"
    fi
else
    echo -e "${YELLOW}! Cannot check app logs${NC}"
fi
echo

echo -e "${BOLD}6. Database Diagnostics${NC}"
if [ "$APP_RUNNING" = true ]; then
    echo "Checking database:"
    DB_STATUS=$(docker exec $APP_CONTAINER bash -c "python -c \"import sqlite3; conn=sqlite3.connect('/app/data/app.db'); cursor=conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'); tables=cursor.fetchall(); print('Tables found:', [t[0] for t in tables]); conn.close()\" 2>&1" || echo "Database error")
    
    if [[ $DB_STATUS == *"Tables found:"* ]]; then
        echo -e "${GREEN}✓ Database connection successful${NC}"
        echo "   $DB_STATUS"
    else
        echo -e "${RED}✗ Database connection failed${NC}"
        echo "   Error: $DB_STATUS"
        
        # Check alternate location
        ALT_DB_STATUS=$(docker exec $APP_CONTAINER bash -c "python -c \"import sqlite3; conn=sqlite3.connect('/app/app.db'); cursor=conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'); tables=cursor.fetchall(); print('Tables found in alternate location:', [t[0] for t in tables]); conn.close()\" 2>&1" || echo "Alternate database error")
        
        if [[ $ALT_DB_STATUS == *"Tables found"* ]]; then
            echo -e "${YELLOW}! Database found at alternate location${NC}"
            echo "   $ALT_DB_STATUS"
        else
            echo -e "${RED}✗ No working database found${NC}"
        fi
    fi
else
    echo -e "${YELLOW}! Cannot check database${NC}"
fi
echo

echo -e "${BOLD}7. Nginx Configuration Analysis${NC}"
if [ "$NGINX_RUNNING" = true ]; then
    echo "Checking Nginx configuration:"
    docker exec $NGINX_CONTAINER nginx -T 2>/dev/null || echo "Cannot dump nginx configuration"
    
    echo "Testing Nginx configuration syntax:"
    docker exec $NGINX_CONTAINER nginx -t 2>&1
    
    echo "Checking proxy configuration:"
    PROXY_CONFIG=$(docker exec $NGINX_CONTAINER grep -r "proxy_pass" /etc/nginx/conf.d/)
    echo "$PROXY_CONFIG"
    
    if echo "$PROXY_CONFIG" | grep -q "app:9000"; then
        echo -e "${GREEN}✓ Nginx configured to proxy to app:9000${NC}"
    elif echo "$PROXY_CONFIG" | grep -q "$APP_IP:9000"; then
        echo -e "${GREEN}✓ Nginx configured to proxy to app IP directly${NC}"
    else
        echo -e "${RED}✗ Nginx proxy configuration may be incorrect${NC}"
    fi
else
    echo -e "${YELLOW}! Cannot check Nginx configuration${NC}"
fi
echo

echo -e "${BOLD}8. External Connectivity Tests${NC}"
echo "Testing direct API connection:"
if curl -s http://localhost:9000/api/health >/dev/null; then
    echo -e "${GREEN}✓ Direct API connection successful${NC}"
    echo "   Response: $(curl -s http://localhost:9000/api/health)"
else
    echo -e "${RED}✗ Direct API connection failed${NC}"
fi

echo "Testing connection through Nginx HTTP:"
if curl -s http://localhost:8080/api/health >/dev/null; then
    echo -e "${GREEN}✓ Nginx HTTP connection successful${NC}"
    echo "   Response: $(curl -s http://localhost:8080/api/health)"
else
    echo -e "${RED}✗ Nginx HTTP connection failed${NC}"
fi

echo "Testing connection through Nginx HTTPS:"
if curl -s -k https://localhost:8443/api/health >/dev/null; then
    echo -e "${GREEN}✓ Nginx HTTPS connection successful${NC}"
    echo "   Response: $(curl -s -k https://localhost:8443/api/health)"
else
    echo -e "${RED}✗ Nginx HTTPS connection failed${NC}"
fi
echo

echo -e "${BOLD}9. Recommended Fixes${NC}"
echo "Based on diagnostics, the following issues and fixes have been identified:"

# Recommend fixes based on diagnostics
FIXES=()

if [ "$APP_RUNNING" = false ] || [ "$NGINX_RUNNING" = false ]; then
    FIXES+=("Container start issues: Run ./scripts/fix_all_issues.sh to restart containers")
fi

if [ "$PERMISSION_ERRORS" = true ]; then
    FIXES+=("Permission errors: Run ./scripts/docker_permissions_fix.sh to fix volume permissions")
fi

if [ "$MISSING_FILES" = true ]; then
    FIXES+=("Missing files: Run ./scripts/setup_templates.sh to create required template files")
fi

if [ "$DB_ERRORS" = true ]; then
    FIXES+=("Database issues: Run ./scripts/database_fix.sh to repair the database")
fi

if [ -n "$APP_RUNNING" ] && [ -n "$NGINX_RUNNING" ] && [ "$APP_NETWORKS" != "$NGINX_NETWORKS" ]; then
    FIXES+=("Network mismatch: Run ./scripts/fix_container_network.sh to fix container networking")
fi

# Display fixes
if [ ${#FIXES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ No critical issues detected${NC}"
else
    echo -e "${YELLOW}! ${#FIXES[@]} issue(s) detected:${NC}"
    
    for i in "${!FIXES[@]}"; do
        echo "$((i+1)). ${FIXES[$i]}"
    done
fi
echo

echo -e "${BOLD}10. One-Command Fix${NC}"
echo "To apply all fixes automatically, run:"
echo -e "${BLUE}./scripts/fix_all_issues.sh${NC}"
echo

echo -e "${GREEN}${BOLD}Diagnostics completed!${NC}"
echo "Use the recommended fixes above to resolve any issues."
echo "For more detailed logs, check: docker logs $APP_CONTAINER"
