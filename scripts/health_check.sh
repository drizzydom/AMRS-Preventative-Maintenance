#!/bin/bash
# =============================================================================
# AMRS Health Check Script
# This script checks the health of all AMRS components
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS System Health Check${NC}"
echo "======================="
echo

# Get ports from arguments or use defaults
APP_PORT=${1:-9000}
HTTP_PORT=${2:-8080}
HTTPS_PORT=${3:-8443}

# Record overall health status
HEALTH_STATUS=true

# Function to check if a service is responding
check_service() {
    local name="$1"
    local url="$2"
    local expected="$3"
    local max_attempts=${4:-3}
    local insecure=${5:-false}
    local attempt=1
    
    echo -e "${BOLD}Checking $name...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        echo -n "Attempt $attempt/$max_attempts: "
        
        # Use curl to check the service, with or without SSL verification
        if [ "$insecure" = true ]; then
            response=$(curl -k -s "$url")
        else
            response=$(curl -s "$url")
        fi
        
        # Check if curl was successful and if response contains expected string
        if [ $? -eq 0 ] && [ -n "$response" ] && echo "$response" | grep -q "$expected"; then
            echo -e "${GREEN}OK${NC}"
            return 0
        else
            echo -e "${YELLOW}Failed${NC}"
            attempt=$((attempt+1))
            sleep 3
        fi
    done
    
    echo -e "${RED}Service $name is not responding properly after $max_attempts attempts${NC}"
    HEALTH_STATUS=false
    return 1
}

# Check Docker container status
echo -e "${BOLD}1. Checking Docker container status...${NC}"

# Check app container
if docker ps | grep -q amrs-maintenance-tracker; then
    echo -e "${GREEN}✓ App container is running${NC}"
else
    echo -e "${RED}✗ App container is not running${NC}"
    HEALTH_STATUS=false
fi

# Check nginx container
if docker ps | grep -q amrs-nginx || docker ps | grep -q nginx; then
    echo -e "${GREEN}✓ Nginx container is running${NC}"
else
    echo -e "${RED}✗ Nginx container is not running${NC}"
    HEALTH_STATUS=false
fi
echo

# Check services
echo -e "${BOLD}2. Checking service endpoints...${NC}"

# Check direct access to Flask app
check_service "Flask API" "http://localhost:$APP_PORT/api/health" "status" 3

# Check access through Nginx (HTTP)
check_service "Nginx HTTP" "http://localhost:$HTTP_PORT/api/health" "status" 3

# Check access through Nginx (HTTPS) - Allow self-signed cert
check_service "Nginx HTTPS" "https://localhost:$HTTPS_PORT/api/health" "status" 3 true
echo

# Check database status
echo -e "${BOLD}3. Checking database status...${NC}"
db_check=$(docker exec amrs-maintenance-tracker bash -c 'sqlite3 /app/data/app.db ".tables" 2>/dev/null || echo "Failed"')

if [ "$db_check" == "Failed" ]; then
    echo -e "${RED}✗ Database check failed${NC}"
    HEALTH_STATUS=false
    
    # Check alternative database location
    alt_db_check=$(docker exec amrs-maintenance-tracker bash -c 'sqlite3 /app/app.db ".tables" 2>/dev/null || echo "Failed"')
    if [ "$alt_db_check" != "Failed" ]; then
        echo -e "${YELLOW}! Found database at alternate location: /app/app.db${NC}"
        echo "   $alt_db_check"
    else
        # Try to identify where the database might be
        db_find=$(docker exec amrs-maintenance-tracker find /app -name "*.db" 2>/dev/null)
        if [ -n "$db_find" ]; then
            echo -e "${YELLOW}! Found database files at:${NC}"
            echo "   $db_find"
        fi
    fi
else
    echo -e "${GREEN}✓ Database exists and contains tables:${NC}"
    echo "   $db_check"
    
    # Check for admin user
    admin_check=$(docker exec amrs-maintenance-tracker bash -c 'sqlite3 /app/data/app.db "SELECT count(*) FROM user WHERE username=\"techsupport\"" 2>/dev/null || echo "0"')
    
    if [ "$admin_check" -eq "0" ]; then
        echo -e "${RED}✗ Admin user not found in database${NC}"
        HEALTH_STATUS=false
    else
        echo -e "${GREEN}✓ Admin user exists in database${NC}"
    fi
fi
echo

# Check file permissions
echo -e "${BOLD}4. Checking file permissions...${NC}"
data_perms=$(docker exec amrs-maintenance-tracker bash -c 'ls -l /app/data/app.db 2>/dev/null | awk "{print \$1}" || echo "Not found"')

if [ "$data_perms" == "Not found" ]; then
    echo -e "${RED}✗ Database file not found at expected location${NC}"
    # Check if it exists at alternate location
    alt_data_perms=$(docker exec amrs-maintenance-tracker bash -c 'ls -l /app/app.db 2>/dev/null | awk "{print \$1}" || echo "Not found"')
    if [ "$alt_data_perms" != "Not found" ]; then
        echo -e "${YELLOW}! Database found at alternate location with permissions: $alt_data_perms${NC}"
    else
        HEALTH_STATUS=false
    fi
else
    if [[ "$data_perms" == *"rw"* ]]; then
        echo -e "${GREEN}✓ Database file has proper permissions${NC}"
    else
        echo -e "${YELLOW}! Database has restricted permissions: $data_perms${NC}"
        echo "  This may cause issues with write access."
        HEALTH_STATUS=false
    fi
fi

# Check template directory permissions
template_perms=$(docker exec amrs-maintenance-tracker bash -c 'ls -ld /app/templates 2>/dev/null | awk "{print \$1}" || echo "Not found"')
if [ "$template_perms" == "Not found" ]; then
    echo -e "${RED}✗ Templates directory not found${NC}"
    HEALTH_STATUS=false
else
    if [[ "$template_perms" == *"rwx"* ]]; then
        echo -e "${GREEN}✓ Templates directory has proper permissions${NC}"
    else
        echo -e "${YELLOW}! Templates directory has restricted permissions: $template_perms${NC}"
        HEALTH_STATUS=false
    fi
fi
echo

# Check for template files
echo -e "${BOLD}5. Checking template files...${NC}"
template_check=$(docker exec amrs-maintenance-tracker bash -c 'ls -la /app/templates/ 2>/dev/null | wc -l || echo "0"')

if [ "$template_check" -le 2 ]; then
    echo -e "${RED}✗ No template files found in container${NC}"
    
    # Check data directory for templates
    data_templates=$(docker exec amrs-maintenance-tracker bash -c 'ls -la /app/data/templates/ 2>/dev/null | wc -l || echo "0"')
    if [ "$data_templates" -gt 2 ]; then
        echo -e "${YELLOW}! Templates found in data directory but not copied to app${NC}"
        echo "   Run: ./scripts/fix_template_permissions.sh"
    else
        echo -e "${RED}✗ No templates found in data directory either${NC}"
        echo "   Run: ./scripts/setup_templates.sh"
    fi
    HEALTH_STATUS=false
else
    echo -e "${GREEN}✓ Found $(($template_check - 2)) template files${NC}"
    # Check for critical templates
    for template in "base.html" "login.html" "index.html"; do
        if ! docker exec amrs-maintenance-tracker bash -c "[ -f /app/templates/$template ]"; then
            echo -e "${RED}✗ Critical template missing: $template${NC}"
            HEALTH_STATUS=false
        fi
    done
fi
echo

# Check for error messages in logs
echo -e "${BOLD}6. Checking for errors in logs...${NC}"
app_errors=$(docker logs --since=1h amrs-maintenance-tracker 2>&1 | grep -i "error\|exception\|failed" | grep -v "DEBUG" | wc -l)
nginx_errors=$(docker logs amrs-nginx 2>&1 | grep -i "error\|failed" | grep -v "worker_connections" | wc -l)

if [ "$app_errors" -gt 0 ]; then
    echo -e "${YELLOW}! Found $app_errors errors/exceptions in app logs${NC}"
    docker logs --since=1h amrs-maintenance-tracker 2>&1 | grep -i "error\|exception\|failed" | grep -v "DEBUG" | head -5
    HEALTH_STATUS=false
else
    echo -e "${GREEN}✓ No obvious errors in app logs${NC}"
fi

if [ "$nginx_errors" -gt 0 ]; then
    echo -e "${YELLOW}! Found $nginx_errors errors in Nginx logs${NC}"
    docker logs amrs-nginx 2>&1 | grep -i "error\|failed" | grep -v "worker_connections" | head -5
    HEALTH_STATUS=false
else
    echo -e "${GREEN}✓ No obvious errors in Nginx logs${NC}"
fi

# Check Flask app binding
echo -e "${BOLD}7. Checking Flask binding and port configuration...${NC}"
binding_check=$(docker exec amrs-maintenance-tracker bash -c 'netstat -tuln 2>/dev/null | grep 9000 || ss -tuln 2>/dev/null | grep 9000 || echo "No binding found"')

if echo "$binding_check" | grep -q "0.0.0.0:9000"; then
    echo -e "${GREEN}✓ Flask app is correctly bound to 0.0.0.0:9000${NC}"
else
    echo -e "${RED}✗ Flask app is not correctly bound to port 9000${NC}"
    echo "   Current binding: $binding_check"
    
    # Check for port conflicts
    ports_in_use=$(docker exec amrs-maintenance-tracker bash -c 'netstat -tuln 2>/dev/null || ss -tuln 2>/dev/null')
    echo -e "${YELLOW}! Ports in use inside container:${NC}"
    echo "$ports_in_use"
    HEALTH_STATUS=false
fi
echo

# Final health status report
echo -e "${BOLD}Health Check Summary:${NC}"
echo "======================="

if [ "$HEALTH_STATUS" = true ]; then
    echo -e "${GREEN}${BOLD}✓ All systems operational!${NC}"
    echo
    echo "Your AMRS system is running correctly and can be accessed at:"
    echo "- HTTP: http://localhost:$HTTP_PORT"
    echo "- HTTPS: https://localhost:$HTTPS_PORT"
    echo "- Direct API: http://localhost:$APP_PORT"
    echo 
    echo "Login with: techsupport / Sm@rty123"
    exit 0
else
    echo -e "${RED}${BOLD}✗ Some issues were detected!${NC}"
    echo
    echo "Please run these commands to fix common issues:"
    echo
    echo "1. Fix template issues: ./scripts/fix_template_permissions.sh"
    echo "2. Fix database issues: ./scripts/database_fix.sh"
    echo "3. Fix binding issues: ./scripts/fix_502_error.sh"
    echo
    echo "For detailed troubleshooting, check app logs:"
    echo "docker logs amrs-maintenance-tracker"
    exit 1
fi
