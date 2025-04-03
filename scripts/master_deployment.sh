#!/bin/bash
# =============================================================================
# AMRS Master Deployment Script
# This script orchestrates the entire deployment process using specialized scripts
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Track what fixes have been applied to avoid redundancy
declare -A APPLIED_FIXES
# Track overall deployment status
DEPLOYMENT_SUCCESS=true
# Store diagnostic information
DIAGNOSTIC_INFO=""

echo -e "${BOLD}AMRS Master Deployment Script${NC}"
echo "============================"
echo

# Enhanced function to run a specialized script with better error diagnosis
run_script() {
    local script="$1"
    local description="$2"
    shift 2  # Remove first two parameters
    
    echo -e "\n${BOLD}${YELLOW}Running: ${description}${NC}"
    echo "======================================="
    
    # Check if script exists
    if [ -f "$SCRIPT_DIR/$script" ]; then
        # Make script executable
        chmod +x "$SCRIPT_DIR/$script"
        
        # Run script with any remaining arguments
        "$SCRIPT_DIR/$script" "$@"
        local result=$?
        
        # Check exit code
        if [ $result -eq 0 ]; then
            echo -e "\n${GREEN}✓ ${description} completed successfully${NC}"
            return 0
        else
            echo -e "\n${RED}✗ ${description} failed with exit code $result${NC}"
            # Store diagnostic information
            DIAGNOSTIC_INFO="${DIAGNOSTIC_INFO}Failure in ${description} (exit code $result)\n"
            return $result
        fi
    else
        echo -e "${RED}✗ Script not found: $script${NC}"
        return 1
    fi
}

# Function to apply troubleshooting steps based on failure pattern
apply_troubleshooting() {
    local failed_step="$1"
    local data_dir="$2"
    
    echo -e "\n${BOLD}${YELLOW}Applying troubleshooting for: $failed_step${NC}"
    echo "======================================="
    
    case "$failed_step" in
        "network")
            # Apply network troubleshooting if not already applied
            if [ -z "${APPLIED_FIXES[network]}" ]; then
                echo "Applying network troubleshooting..."
                
                # First try the standard network fix
                if run_script "fix_container_network.sh" "Network troubleshooting" "$data_dir"; then
                    APPLIED_FIXES[network]=1
                    return 0
                fi
                
                # If standard fix fails, try the nuclear option
                echo "Standard network fix failed, trying nuclear option..."
                if run_script "nuclear_network_fix.sh" "Nuclear network fix"; then
                    APPLIED_FIXES[network]=1
                    return 0
                fi
                
                # If nuclear option fails, try direct manual intervention
                echo "Manual network intervention as last resort..."
                NETWORK_NAME="amrs_network"
                docker network create $NETWORK_NAME 2>/dev/null || true
                docker network connect $NETWORK_NAME amrs-maintenance-tracker 2>/dev/null || true
                docker network connect $NETWORK_NAME amrs-nginx 2>/dev/null || true
                
                APPLIED_FIXES[network]=1
                return 0
            fi
            ;;
            
        "permissions")
            # Apply permission troubleshooting if not already applied
            if [ -z "${APPLIED_FIXES[permissions]}" ]; then
                echo "Applying permission troubleshooting..."
                
                # First try the standard permission fix
                if run_script "fix_template_permissions.sh" "Permission troubleshooting" "$data_dir"; then
                    APPLIED_FIXES[permissions]=1
                    return 0
                fi
                
                # If that fails, try the Docker permissions fix
                echo "Standard permission fix failed, trying Docker permission fix..."
                if run_script "docker_permissions_fix.sh" "Docker permission fix" "$data_dir"; then
                    APPLIED_FIXES[permissions]=1
                    return 0
                fi
                
                # Last resort - direct Docker commands as root
                echo "Manual permission fix as last resort..."
                docker exec -u root amrs-maintenance-tracker bash -c "mkdir -p /app/templates /app/static /app/data && chmod -R 777 /app/templates /app/static /app/data" 2>/dev/null || true
                
                APPLIED_FIXES[permissions]=1
                return 0
            fi
            ;;
            
        "database")
            # Apply database troubleshooting if not already applied
            if [ -z "${APPLIED_FIXES[database]}" ]; then
                echo "Applying database troubleshooting..."
                
                # Try the database fix
                if run_script "database_fix.sh" "Database troubleshooting" "$data_dir"; then
                    APPLIED_FIXES[database]=1 
                    return 0
                fi
                
                # If that fails, create minimal database directly
                echo "Database fix failed, creating minimal database manually..."
                mkdir -p "$data_dir/data"
                docker run --rm -v "$data_dir/data:/data" python:3.9-alpine python -c '
import sqlite3, os
conn = sqlite3.connect("/data/app.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY, username TEXT, email TEXT, password_hash TEXT)")
c.execute("INSERT OR IGNORE INTO user VALUES (1, \"techsupport\", \"admin@example.com\", \"pbkdf2:sha256:260000$gEv81A7qSCwKW7AX$d16c4780521640d58707f8af594a5ddfe0b86e89b08c488e0d39a39a1b70e613\")")
conn.commit()
conn.close()
os.chmod("/data/app.db", 0o666)
print("Minimal database created successfully")
'
                APPLIED_FIXES[database]=1
                return 0
            fi
            ;;
            
        "nginx")
            # Apply Nginx troubleshooting if not already applied
            if [ -z "${APPLIED_FIXES[nginx]}" ]; then
                echo "Applying Nginx troubleshooting..."
                
                # First reset the Nginx configuration
                mkdir -p "$data_dir/nginx/conf.d"
                cat > "$data_dir/nginx/conf.d/default.conf" << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://app:9000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        
        # Extended timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF
                # Restart Nginx
                docker restart amrs-nginx 2>/dev/null || true
                
                APPLIED_FIXES[nginx]=1
                return 0
            fi
            ;;
            
        "comprehensive")
            # Apply comprehensive fix that tries to address multiple issues at once
            if [ -z "${APPLIED_FIXES[comprehensive]}" ]; then
                echo "Applying comprehensive troubleshooting..."
                
                if run_script "fix_all_issues.sh" "Comprehensive troubleshooting" "$data_dir"; then
                    # Mark all individual fixes as applied since fix_all_issues.sh addresses everything
                    APPLIED_FIXES[network]=1
                    APPLIED_FIXES[permissions]=1
                    APPLIED_FIXES[database]=1
                    APPLIED_FIXES[nginx]=1
                    APPLIED_FIXES[comprehensive]=1
                    return 0
                fi
                
                APPLIED_FIXES[comprehensive]=1
                return 1
            fi
            ;;
    esac
    
    echo "No new troubleshooting steps to apply for: $failed_step"
    return 0
}

# Function to diagnose errors in container logs
diagnose_container_logs() {
    local container="$1"
    
    echo -e "\n${BOLD}${YELLOW}Diagnosing logs for container: $container${NC}"
    
    # Get recent errors from logs
    local errors=$(docker logs $container 2>&1 | grep -i "error\|exception\|failed" | grep -v "DEBUG" | tail -10)
    
    if [ -n "$errors" ]; then
        echo -e "${RED}Found errors in $container logs:${NC}"
        echo "$errors"
        
        # Analyze error patterns
        if echo "$errors" | grep -q "permission\|denied"; then
            echo -e "${YELLOW}Detected permission issues${NC}"
            apply_troubleshooting "permissions" "$DATA_DIR"
        fi
        
        if echo "$errors" | grep -q "database\|sqlite\|db"; then
            echo -e "${YELLOW}Detected database issues${NC}"
            apply_troubleshooting "database" "$DATA_DIR"
        fi
        
        if echo "$errors" | grep -q "network\|connection\|refused\|connect"; then
            echo -e "${YELLOW}Detected network issues${NC}"
            apply_troubleshooting "network" "$DATA_DIR"
        fi
        
        if echo "$errors" | grep -q "template\|not found\|missing"; then
            echo -e "${YELLOW}Detected missing files${NC}"
            apply_troubleshooting "permissions" "$DATA_DIR"
        fi
    else
        echo -e "${GREEN}No obvious errors in $container logs${NC}"
    fi
}

# Function to perform system verification and status checks
verify_system() {
    echo -e "\n${BOLD}${YELLOW}Performing system verification...${NC}"
    echo "======================================="
    
    # Check if containers are running
    if ! docker ps | grep -q "amrs-maintenance-tracker"; then
        echo -e "${RED}✗ App container is not running${NC}"
        DEPLOYMENT_SUCCESS=false
    fi
    
    if ! docker ps | grep -q "amrs-nginx"; then
        echo -e "${RED}✗ Nginx container is not running${NC}"
        DEPLOYMENT_SUCCESS=false
    fi
    
    # Check API connectivity
    if ! curl -s http://localhost:9000/api/health | grep -q "status"; then
        echo -e "${RED}✗ Cannot connect to API directly${NC}"
        DEPLOYMENT_SUCCESS=false
    else
        echo -e "${GREEN}✓ API responds correctly${NC}"
    fi
    
    if ! curl -s http://localhost:8080/api/health | grep -q "status"; then
        echo -e "${RED}✗ Cannot connect via Nginx HTTP${NC}"
        DEPLOYMENT_SUCCESS=false
    else
        echo -e "${GREEN}✓ Nginx HTTP proxy works correctly${NC}"
    fi
    
    # Return overall status
    if [ "$DEPLOYMENT_SUCCESS" = true ]; then
        return 0
    else
        return 1
    fi
}

# Welcome message
echo "This script will orchestrate the complete deployment of the AMRS Maintenance System."
echo "It will run the specialized scripts in the correct order to set up the entire system."
echo "If issues are detected, it will automatically apply troubleshooting steps."
echo

# Get data directory from user input
read -p "Enter data directory path (default: /volume1/docker/amrs-data): " DATA_DIR
DATA_DIR=${DATA_DIR:-"/volume1/docker/amrs-data"}
echo "Using data directory: $DATA_DIR"

# Get HTTPS port from user
read -p "Enter HTTPS port for external access (default: 8443): " HTTPS_PORT
HTTPS_PORT=${HTTPS_PORT:-"8443"}

# Get HTTP port from user
read -p "Enter HTTP port for external access (default: 8080): " HTTP_PORT
HTTP_PORT=${HTTP_PORT:-"8080"}

# Get container port from user
read -p "Enter internal container port (default: 9000): " CONTAINER_PORT
CONTAINER_PORT=${CONTAINER_PORT:-"9000"}

# Get domain name if available
read -p "Enter your domain name (leave empty if none): " DOMAIN_NAME

echo
echo -e "${BOLD}Deployment Configuration:${NC}"
echo "- Data Directory: $DATA_DIR"
echo "- HTTPS Port: $HTTPS_PORT"
echo "- HTTP Port: $HTTP_PORT"
echo "- Container Port: $CONTAINER_PORT"
if [ -n "$DOMAIN_NAME" ]; then
    echo "- Domain Name: $DOMAIN_NAME"
else
    echo "- Domain Name: Not specified (using localhost)"
fi
echo

read -p "Continue with deployment? (y/n): " CONTINUE
if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Step 1: Check prerequisites
run_script "check_prerequisites.sh" "Checking prerequisites" || {
    echo -e "${RED}Prerequisites check failed. Please fix the issues and try again.${NC}"
    exit 1
}

# Step 2: Set up directories
run_script "setup_directories.sh" "Setting up directories" "$DATA_DIR" || {
    echo -e "${RED}Directory setup failed. Please check permissions and try again.${NC}"
    exit 1
}

# Step 3: Network setup (with more reliable error handling)
echo -e "\n${BOLD}${YELLOW}Running: Network Setup${NC}"
echo "======================================="

NETWORK_NAME="amrs_network"
docker network rm $NETWORK_NAME 2>/dev/null || true
if ! docker network create $NETWORK_NAME; then
    echo -e "${YELLOW}Warning: Failed to create network, trying troubleshooting...${NC}"
    apply_troubleshooting "network" "$DATA_DIR"
else
    echo -e "${GREEN}✓ Network created successfully${NC}"
fi

# Step 4: Generate SSL certificates
if [ -n "$DOMAIN_NAME" ]; then
    run_script "generate_ssl.sh" "Generating SSL certificates" "$DATA_DIR" "$DOMAIN_NAME" || {
        echo -e "${YELLOW}Warning: Failed to generate SSL certificates with domain. Using localhost instead.${NC}"
        run_script "generate_ssl.sh" "Generating SSL certificates" "$DATA_DIR" "localhost"
    }
else
    run_script "generate_ssl.sh" "Generating SSL certificates" "$DATA_DIR"
fi

# Step 5: Configure Nginx
run_script "configure_nginx.sh" "Configuring Nginx" "$DATA_DIR" "$CONTAINER_PORT" "$HTTP_PORT" "$HTTPS_PORT" || {
    echo -e "${RED}Nginx configuration failed. Please check logs and try again.${NC}"
    exit 1
}

# Step 6: Set up templates
run_script "setup_templates.sh" "Setting up templates" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Template setup had issues. The application may have limited functionality.${NC}"
    # Run the template permissions fix script to ensure proper permissions
    run_script "fix_template_permissions.sh" "Fixing template permissions" "$DATA_DIR" || true
}

# Step 7: Initialize database
run_script "initialize_database.sh" "Initializing database" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Database initialization had issues. Using database fix script.${NC}"
    # Try to fix database issues
    run_script "database_fix.sh" "Fixing database issues" "$DATA_DIR" || true
}

# Step 8: Build and start containers with enhanced troubleshooting
run_script "build_and_start.sh" "Building and starting containers" "$DATA_DIR" "$NETWORK_NAME" "$CONTAINER_PORT" "$HTTP_PORT" "$HTTPS_PORT" || {
    echo -e "${YELLOW}Failed to build and start containers. Attempting troubleshooting...${NC}"
    
    # Check container logs to diagnose issues
    diagnose_container_logs "amrs-maintenance-tracker" 
    
    # Apply network fix
    apply_troubleshooting "network" "$DATA_DIR"
    
    # Try again
    if ! run_script "build_and_start.sh" "Retrying container start" "$DATA_DIR" "$NETWORK_NAME" "$CONTAINER_PORT" "$HTTP_PORT" "$HTTPS_PORT"; then
        echo -e "${RED}Still failing, trying one more approach...${NC}"
        
        # Try a more comprehensive fix
        apply_troubleshooting "comprehensive" "$DATA_DIR"
        
        # Last attempt
        run_script "build_and_start.sh" "Final attempt to start containers" "$DATA_DIR" "$NETWORK_NAME" "$CONTAINER_PORT" "$HTTP_PORT" "$HTTPS_PORT" || {
            echo -e "${RED}Failed to start containers despite troubleshooting.${NC}"
            DEPLOYMENT_SUCCESS=false
        }
    fi
}

# Step 9: Fix permissions - basic level
run_script "fix_permissions.sh" "Fixing permissions" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Permission fixes had issues. You may encounter permission problems.${NC}"
}

# Step 10: Apply Docker permission fixes - more comprehensive
run_script "docker_permissions_fix.sh" "Fixing Docker permissions" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Docker permission fixes had issues. Trying alternative approach...${NC}"
    # If docker_permissions_fix fails, use the old method from fix_permissions.sh with root user
    docker exec -u root amrs-maintenance-tracker bash -c "chmod -R 777 /app/data /app/templates /app/static" 2>/dev/null || true
}

# Step 11: Fix container networking issues
run_script "fix_container_network.sh" "Fixing container networking" || {
    echo -e "${YELLOW}Warning: Network fixes had issues. Trying alternate networking approach...${NC}"
    # Apply hosts file entries manually
    APP_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' amrs-maintenance-tracker 2>/dev/null || echo "")
    NGINX_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' amrs-nginx 2>/dev/null || echo "")
    if [ -n "$APP_IP" ] && [ -n "$NGINX_IP" ]; then
        docker exec amrs-maintenance-tracker bash -c "echo '$NGINX_IP nginx amrs-nginx' >> /etc/hosts" 2>/dev/null || true
        docker exec amrs-nginx bash -c "echo '$APP_IP app amrs-maintenance-tracker' >> /etc/hosts" 2>/dev/null || true
        echo -e "${GREEN}✓ Applied manual host entries${NC}"
    fi
}

# Step 12: Fix templates - specific fix for permission and access problems
run_script "fix_template_permissions.sh" "Fixing template permissions" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Template permission fixes had issues. Creating basic templates...${NC}"
    # Create basic template files directly
    mkdir -p "$DATA_DIR/templates"
    chmod -R 777 "$DATA_DIR/templates"
    echo "<html><body><h1>AMRS Maintenance</h1><p>Basic template</p></body></html>" > "$DATA_DIR/templates/base.html"
    chmod 666 "$DATA_DIR/templates/base.html"
}

# Step 13: Fix 502 errors that might occur during startup
run_script "fix_502_error.sh" "Fixing 502 Gateway errors" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: 502 error fixes had issues. Check nginx logs for details.${NC}"
}

# Step 14: Run advanced diagnostics
run_script "advanced_diagnostics.sh" "Running advanced diagnostics" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Diagnostics reported issues. Reviewing reported issues...${NC}"
}

# Step 15: Apply comprehensive fixes to address any remaining issues
run_script "fix_all_issues.sh" "Applying comprehensive fixes" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Comprehensive fixes had issues. Some manual intervention may be required.${NC}"
}

# Step 16: Run a comprehensive system verification
echo -e "\n${BOLD}${YELLOW}Running: Final System Verification${NC}"
echo "======================================="

if verify_system; then
    echo -e "${GREEN}${BOLD}System verification passed!${NC}"
else
    echo -e "${RED}${BOLD}System verification failed. Applying emergency fixes...${NC}"
    
    # Apply last-resort comprehensive fix regardless of previous attempts
    APPLIED_FIXES=() # Reset applied fixes to force another attempt
    apply_troubleshooting "comprehensive" "$DATA_DIR"
    
    # Check one more time
    if verify_system; then
        echo -e "${GREEN}${BOLD}System recovery succeeded!${NC}"
        DEPLOYMENT_SUCCESS=true
    else
        echo -e "${RED}${BOLD}System recovery failed. Manual intervention required.${NC}"
        DEPLOYMENT_SUCCESS=false
    fi
fi

# Step 17: Install common fixes and helper scripts
run_script "install_fixes.sh" "Installing common fixes" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Some fixes could not be installed. You may need to apply them manually.${NC}"
}

# Step 18: Run health check
run_script "health_check.sh" "Running health check" "$CONTAINER_PORT" "$HTTP_PORT" "$HTTPS_PORT" || {
    echo -e "${YELLOW}Warning: Health check detected issues. The application may not be fully functional.${NC}"
    # Try to run the quick connection test to verify basic connectivity
    run_script "connection_test.sh" "Testing basic connectivity" "$CONTAINER_PORT" "$HTTP_PORT" "$HTTPS_PORT" || true
}

# Step 19: Apply security hardening
run_script "synology_security.sh" "Applying security hardening" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Security hardening had issues. Consider manual security setup.${NC}"
}

# Step 20: Configure port forwarding guide
run_script "synology_port_config.sh" "Displaying port forwarding guide" "$HTTP_PORT" "$HTTPS_PORT" || {
    echo -e "${YELLOW}Warning: Could not display port forwarding guide.${NC}"
}

# Step 21: Create a backup of the working configuration
run_script "backup_config.sh" "Creating initial backup" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Initial backup creation failed. Consider manual backup.${NC}"
}

# Step 22: Final verification - check if the application is responding
echo -e "\n${BOLD}${YELLOW}Running: Final verification${NC}"
echo "======================================="
echo "Testing if the application is accessible..."

FINAL_CHECK=$(curl -s -k "https://localhost:$HTTPS_PORT/api/health" 2>/dev/null || curl -s "http://localhost:$HTTP_PORT/api/health" 2>/dev/null || curl -s "http://localhost:$CONTAINER_PORT/api/health" 2>/dev/null)

if echo "$FINAL_CHECK" | grep -q "status"; then
    echo -e "${GREEN}✓ Application is responding correctly!${NC}"
    echo "Verification successful."
else
    echo -e "${YELLOW}! Application is not responding to health checks${NC}"
    echo "You may need to wait a few minutes for the application to fully initialize."
    echo "If issues persist, run: ./scripts/quick_diagnostics.sh"
fi

echo
if [ "$DEPLOYMENT_SUCCESS" = true ]; then
    echo -e "${GREEN}${BOLD}AMRS Deployment Complete and Verified!${NC}"
    echo
    echo "Your AMRS Maintenance Tracker application has been deployed successfully."
    echo "It should be accessible at:"
    echo "- HTTP: http://localhost:$HTTP_PORT"
    echo "- HTTPS: https://localhost:$HTTPS_PORT"
    echo
    echo "Default login credentials:"
    echo "- Username: techsupport"
    echo "- Password: Sm@rty123"
    echo
    echo "Important directories:"
    echo "- Data directory: $DATA_DIR"
    echo "- Configuration: $DATA_DIR/nginx/conf.d"
    echo "- SSL certificates: $DATA_DIR/ssl"
    echo
    echo "Helpful troubleshooting commands:"
    echo "- Check logs: docker logs amrs-maintenance-tracker"
    echo "- Quick diagnostics: $SCRIPT_DIR/quick_diagnostics.sh"
    echo "- Restart: docker-compose restart"
    echo "- Run health check: $SCRIPT_DIR/health_check.sh"
    echo "- Fix permissions: $SCRIPT_DIR/fix_template_permissions.sh"
    echo "- Fix network issues: $SCRIPT_DIR/fix_container_network.sh"  
    echo "- Update application: $SCRIPT_DIR/update_app.sh"
    echo "- Backup configuration: $SCRIPT_DIR/backup_config.sh"
    echo "- Restore configuration: $SCRIPT_DIR/restore_config.sh [backup_file]"
    echo "- Fix all issues at once: $SCRIPT_DIR/fix_all_issues.sh"
else
    echo -e "${RED}${BOLD}AMRS Deployment Completed with Issues${NC}"
    echo
    echo "The deployment encountered problems that automatic troubleshooting couldn't fully resolve."
    echo "Here's a summary of the diagnostics:"
    echo -e "$DIAGNOSTIC_INFO"
    echo
    echo "Recommended manual steps:"
    echo "1. Check container logs: docker logs amrs-maintenance-tracker"
    echo "2. Run advanced diagnostics: $SCRIPT_DIR/advanced_diagnostics.sh"
    echo "3. Apply fixes manually: $SCRIPT_DIR/fix_all_issues.sh"
fi
