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

echo -e "${BOLD}AMRS Master Deployment Script${NC}"
echo "============================"
echo

# Function to run a specialized script
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
        
        # Check exit code
        if [ $? -eq 0 ]; then
            echo -e "\n${GREEN}✓ ${description} completed successfully${NC}"
            return 0
        else
            echo -e "\n${RED}✗ ${description} failed${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Script not found: $script${NC}"
        return 1
    fi
}

# Welcome message
echo "This script will orchestrate the complete deployment of the AMRS Maintenance System."
echo "It will run the specialized scripts in the correct order to set up the entire system."
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

# Step 3: Clean up any existing Docker networks that might conflict
echo -e "\n${BOLD}${YELLOW}Running: Nuclear Network Cleanup${NC}"
echo "======================================="
echo "This will remove any conflicting Docker networks..."

# First disconnect all containers from the network
NETWORK_NAME="amrs_network"
echo "Disconnecting any containers from network: $NETWORK_NAME"
CONNECTED_CONTAINERS=$(docker network inspect $NETWORK_NAME -f '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
for container in $CONNECTED_CONTAINERS; do
    docker network disconnect -f $NETWORK_NAME $container 2>/dev/null || true
done

# Remove the network if it exists
docker network rm $NETWORK_NAME 2>/dev/null || true
docker network prune -f

# Create a fresh network
docker network create $NETWORK_NAME || {
    echo -e "${RED}Failed to create network. Using default bridge network.${NC}"
    NETWORK_NAME="bridge"
}

echo -e "${GREEN}✓ Network cleanup completed${NC}"
echo "$NETWORK_NAME" > /tmp/amrs_network_name

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
}

# Step 7: Initialize database
run_script "initialize_database.sh" "Initializing database" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Database initialization had issues. Database will be created on first run.${NC}"
}

# Step 8: Build and start containers
run_script "build_and_start.sh" "Building and starting containers" "$DATA_DIR" "$NETWORK_NAME" "$CONTAINER_PORT" "$HTTP_PORT" "$HTTPS_PORT" || {
    echo -e "${RED}Failed to build and start containers. Running nuclear network fix...${NC}"
    
    # Run nuclear network fix
    run_script "nuclear_network_fix.sh" "Running nuclear network fix" "$NETWORK_NAME"
    
    # Try build and start again with fixed network
    run_script "build_and_start.sh" "Retrying build and start with fixed network" "$DATA_DIR" "$NETWORK_NAME" "$CONTAINER_PORT" "$HTTP_PORT" "$HTTPS_PORT" || {
        echo -e "${RED}Failed to start containers even after network fix. Please check logs manually.${NC}"
        exit 1
    }
}

# Step 9: Fix permissions
run_script "fix_permissions.sh" "Fixing permissions" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Permission fixes had issues. You may encounter permission problems.${NC}"
}

# Step 10: Install common fixes
run_script "install_fixes.sh" "Installing common fixes" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Some fixes could not be installed. You may need to apply them manually.${NC}"
}

# Step 11: Run health check
run_script "health_check.sh" "Running health check" "$CONTAINER_PORT" "$HTTP_PORT" "$HTTPS_PORT" || {
    echo -e "${YELLOW}Warning: Health check detected issues. The application may not be fully functional.${NC}"
}

# Step 12: Apply security hardening (new step)
run_script "synology_security.sh" "Applying security hardening" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Security hardening had issues. Consider manual security setup.${NC}"
}

# Step 13: Configure port forwarding guide (new step, informational only)
run_script "synology_port_config.sh" "Displaying port forwarding guide" "$HTTP_PORT" "$HTTPS_PORT" || {
    echo -e "${YELLOW}Warning: Could not display port forwarding guide.${NC}"
}

# Step 14: Create a backup of the working configuration (new step)
run_script "backup_config.sh" "Creating initial backup" "$DATA_DIR" || {
    echo -e "${YELLOW}Warning: Initial backup creation failed. Consider manual backup.${NC}"
}

echo
echo -e "${GREEN}${BOLD}AMRS Deployment Complete!${NC}"
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
echo "Helpful commands:"
echo "- Check logs: docker logs amrs-maintenance-tracker"
echo "- Restart: docker-compose restart"
echo "- Run health check: $SCRIPT_DIR/health_check.sh"
echo "- Update application: $SCRIPT_DIR/update_app.sh"
echo "- Backup configuration: $SCRIPT_DIR/backup_config.sh"
echo "- Restore configuration: $SCRIPT_DIR/restore_config.sh [backup_file]"
