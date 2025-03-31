#!/bin/bash
# =============================================================================
# AMRS Preventative Maintenance - Complete Setup Script
# 
# This script automates the full setup process with minimal user intervention.
# =============================================================================

set -e  # Exit on error

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Default values
DEFAULT_DATA_DIR="/volume1/docker/amrs-data"
DEFAULT_PORT=9000
DEFAULT_EXTERNAL_PORT_HTTPS=8443  # Changed from 443 to 8443 to avoid conflict
DEFAULT_EXTERNAL_PORT_HTTP=8080   # Changed from 80 to 8080 to avoid conflict

# Print header
echo -e "${BOLD}${BLUE}"
echo "======================================================"
echo "  AMRS Preventative Maintenance - Complete Setup"
echo "======================================================"
echo -e "${NC}"

# Function to prompt for input with a default value
prompt_with_default() {
    local prompt_text="$1"
    local default_value="$2"
    local var_name="$3"
    
    read -p "$prompt_text [$default_value]: " input
    if [ -z "$input" ]; then
        eval "$var_name=$default_value"
    else
        eval "$var_name=$input"
    fi
}

# Function to copy a directory with rsync if available, otherwise with scp
copy_directory() {
    local src="$1"
    local dst="$2"
    local host="$3"
    local user="$4"
    
    # Create destination directory
    if [[ -n "$host" ]]; then
        ssh ${user}@${host} "mkdir -p ${dst}"
        
        # Copy files with rsync if available (more efficient)
        if command -v rsync &> /dev/null; then
            echo "Using rsync to copy ${src} to ${host}:${dst}"
            rsync -avz --progress ${src}/ ${user}@${host}:${dst}/
        else
            echo "Using scp to copy ${src} to ${host}:${dst}"
            scp -r ${src}/* ${user}@${host}:${dst}/
        fi
    else
        # Local copy
        mkdir -p "${dst}"
        cp -r "${src}/"* "${dst}/"
    fi
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Warning: This script might need root privileges for some operations.${NC}"
    echo "If you encounter permission errors, please run with sudo."
    echo
fi

# Check prerequisites
echo -e "${BOLD}Checking prerequisites...${NC}"

# Determine if we're running on Synology or a remote system
if [ -d "/volume1" ] && [ -f "/etc/synoinfo.conf" ]; then
    IS_SYNOLOGY=true
    echo -e "${GREEN}✓ Running directly on a Synology NAS${NC}"
else
    IS_SYNOLOGY=false
    echo -e "${YELLOW}! Not running on a Synology NAS. Will attempt remote setup.${NC}"
    
    # Check for SSH and SCP/rsync
    if ! command -v ssh &> /dev/null; then
        echo -e "${RED}Error: SSH client not installed. Required for remote setup.${NC}"
        exit 1
    fi
fi

# Check for Docker if running on Synology
if [ "$IS_SYNOLOGY" = true ]; then
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed.${NC}"
        echo "Please install Docker first through Synology's Package Center."
        exit 1
    fi
fi

echo -e "${GREEN}✓ Prerequisites satisfied${NC}"
echo

# Get connection info if running remotely
if [ "$IS_SYNOLOGY" = false ]; then
    echo -e "${BOLD}Synology Connection Information:${NC}"
    prompt_with_default "Enter Synology IP address" "192.168.1.x" SYNOLOGY_IP
    prompt_with_default "Enter Synology username" "admin" SYNOLOGY_USER
    
    echo "Testing SSH connection to Synology..."
    if ! ssh -o BatchMode=yes -o ConnectTimeout=5 ${SYNOLOGY_USER}@${SYNOLOGY_IP} "echo Connected successfully"; then
        echo -e "${RED}Error: Cannot connect to Synology. Please check your connection details and SSH settings.${NC}"
        echo "Make sure SSH is enabled in Control Panel → Terminal & SNMP → Terminal"
        exit 1
    fi
    echo -e "${GREEN}✓ SSH connection successful${NC}"
fi

# Get configuration
echo -e "${BOLD}Configuration:${NC}"
prompt_with_default "Enter your DDNS hostname (e.g. your-domain.synology.me)" "" DDNS_HOSTNAME
if [ "$IS_SYNOLOGY" = true ]; then
    # Replace the hostname -I command with more compatible alternatives
    if command -v hostname &> /dev/null && hostname -I &> /dev/null; then
        SYNOLOGY_IP=$(hostname -I | awk '{print $1}')
    elif command -v ip &> /dev/null; then
        SYNOLOGY_IP=$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d/ -f1 | head -n 1)
    elif command -v ifconfig &> /dev/null; then
        SYNOLOGY_IP=$(ifconfig | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | head -n 1)
    else
        SYNOLOGY_IP="127.0.0.1"  # Fallback to localhost if no method works
        echo -e "${YELLOW}Warning: Could not automatically determine IP address.${NC}"
    fi
    echo "Detected Synology IP address: $SYNOLOGY_IP"
fi
prompt_with_default "Enter path for persistent data" "$DEFAULT_DATA_DIR" DATA_DIR
prompt_with_default "Enter container internal port" "$DEFAULT_PORT" CONTAINER_PORT
prompt_with_default "Enter external HTTPS port (for Nginx)" "$DEFAULT_EXTERNAL_PORT_HTTPS" EXTERNAL_PORT_HTTPS
prompt_with_default "Enter external HTTP port (for Nginx)" "$DEFAULT_EXTERNAL_PORT_HTTP" EXTERNAL_PORT_HTTP
echo -e "${YELLOW}Note: Ports 80 and 443 are typically used by Synology DSM. Using ports $EXTERNAL_PORT_HTTP and $EXTERNAL_PORT_HTTPS instead.${NC}"

# DDNS Configuration
echo -e "${BOLD}DDNS Configuration:${NC}"
prompt_with_default "Configure DDNS automatically? (yes/no)" "yes" CONFIGURE_DDNS
if [[ $CONFIGURE_DDNS =~ ^[Yy]([Ee][Ss])?$ ]]; then
    echo "Available DDNS Providers:"
    echo "1. Synology DDNS"
    echo "2. No-IP"
    echo "3. DuckDNS"
    echo "4. Dynu"
    echo "5. Skip (already configured)"
    read -p "Select DDNS provider (1-5): " DDNS_PROVIDER
    
    if [ "$DDNS_PROVIDER" != "5" ]; then
        prompt_with_default "Enter DDNS hostname" "$DDNS_HOSTNAME" DDNS_HOSTNAME
        prompt_with_default "Enter DDNS username/email" "" DDNS_USERNAME
        read -s -p "Enter DDNS password: " DDNS_PASSWORD
        echo ""
        
        if [ "$IS_SYNOLOGY" = true ]; then
            echo -e "${BOLD}Setting up DDNS on Synology...${NC}"
            # Create script in current directory instead of /tmp
            DDNS_SCRIPT="./setup_ddns_temp.sh"
            cat > $DDNS_SCRIPT << EOSCRIPT
#!/bin/bash
PROVIDER_MAP=("" "Synology" "No-IP" "DuckDNS" "Dynu")
PROVIDER="\${PROVIDER_MAP[$DDNS_PROVIDER]}"

echo "Configuring DDNS with provider: \$PROVIDER"
echo "Hostname: $DDNS_HOSTNAME"
SUCCESS=false

# Try the synoddns command first (newer DSM versions)
if command -v synoddns &> /dev/null; then
    echo "Using synoddns command..."
    synoddns --set-ddns \
        --hostname "$DDNS_HOSTNAME" \
        --username "$DDNS_USERNAME" \
        --password "$DDNS_PASSWORD" \
        --provider "\$PROVIDER"
    if [ \$? -eq 0 ]; then
        echo "DDNS configuration successful with synoddns."
        SUCCESS=true
    else
        echo "synoddns command failed, trying alternative method."
    fi
fi

# If synoddns failed or doesn't exist, try configuration file method
if [ "\$SUCCESS" = false ]; then
    echo "Using configuration file method..."
    CONFIG_FILES=("/etc/ddns.conf" "/usr/syno/etc/ddns_provider.conf" "/usr/syno/etc/ddns.conf")
    for CONFIG_FILE in "\${CONFIG_FILES[@]}"; do
        if [ -f "\$CONFIG_FILE" ]; then
            echo "Found DDNS configuration at \$CONFIG_FILE"
            cp "\$CONFIG_FILE" "\$CONFIG_FILE.bak"
            grep -v "^$DDNS_HOSTNAME" "\$CONFIG_FILE.bak" > "\$CONFIG_FILE"
            echo "$DDNS_HOSTNAME,$DDNS_USERNAME,$DDNS_PASSWORD,\$PROVIDER" >> "\$CONFIG_FILE"
            SUCCESS=true
            break
        fi
    done
fi

# Restart DDNS service if we made changes
if [ "\$SUCCESS" = true ]; then
    echo "Restarting DDNS service..."
    if command -v synoservice &> /dev/null; then
        synoservice --restart ddns
        echo "DDNS service restarted."
    else
        echo "Warning: Could not restart DDNS service automatically."
        echo "You may need to restart it manually from DSM."
    fi
fi

# Validate DDNS setup
echo "Validating DDNS setup..."
sleep 5  # Give the service time to update
if ping -c 1 "$DDNS_HOSTNAME" &> /dev/null; then
    echo "DDNS validation successful - hostname resolves to an IP address."
else
    echo "Warning: Could not verify hostname resolution immediately."
    echo "This is normal as DNS propagation can take time (up to 24 hours)."
    echo "You can check status later with: ping $DDNS_HOSTNAME"
fi

if [ "\$SUCCESS" = true ]; then
    exit 0
else
    echo "Failed to configure DDNS automatically."
    echo "Please configure DDNS manually through DSM Control Panel."
    exit 1
fi
EOSCRIPT
            chmod +x $DDNS_SCRIPT
            
            # Execute directly without sudo if possible, or use sh to execute it
            if [ "$EUID" -eq 0 ]; then
                # Already running as root
                if $DDNS_SCRIPT; then
                    echo -e "${GREEN}✓ DDNS configured successfully${NC}"
                else
                    echo -e "${RED}! DDNS configuration had issues. Check output above for details.${NC}"
                    echo "You may need to configure DDNS manually through DSM Control Panel."
                fi
            else
                # Try with sh instead of sudo
                echo "Attempting to execute script with sh..."
                if sh $DDNS_SCRIPT; then
                    echo -e "${GREEN}✓ DDNS configured successfully${NC}"
                else
                    echo -e "${RED}! DDNS configuration had issues. Check output above for details.${NC}"
                    echo "You may need to configure DDNS manually through DSM Control Panel."
                fi
            fi
            
            # Clean up
            rm $DDNS_SCRIPT
        fi
    fi
fi

# SSL Certificate Configuration
echo -e "${BOLD}SSL Certificate Configuration:${NC}"
prompt_with_default "Configure SSL certificate automatically? (yes/no)" "yes" CONFIGURE_SSL
if [[ $CONFIGURE_SSL =~ ^[Yy]([Ee][Ss])?$ ]]; then
    echo "Certificate options:"
    echo "1. Generate self-signed certificate (for testing)"
    echo "2. Use existing Synology Let's Encrypt certificate"
    echo "3. Set up new Let's Encrypt certificate through Synology"
    echo "4. Skip (use existing certificates)"
    read -p "Select certificate option (1-4): " CERT_OPTION
    
    # Create SSL directory if it doesn't exist
    mkdir -p "$DATA_DIR/ssl"
    
    case $CERT_OPTION in
        1)
            echo -e "${BOLD}Generating self-signed certificate...${NC}"
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout "$DATA_DIR/ssl/privkey.pem" \
                -out "$DATA_DIR/ssl/fullchain.pem" \
                -subj "/CN=$DDNS_HOSTNAME" \
                -addext "subjectAltName=DNS:$DDNS_HOSTNAME,DNS:localhost"
            echo -e "${GREEN}✓ Self-signed certificate created${NC}"
            ;;
        2)
            echo -e "${BOLD}Locating existing Let's Encrypt certificate...${NC}"
            if [ "$IS_SYNOLOGY" = true ]; then
                # Create script in current directory instead of /tmp
                CERT_SCRIPT="./find_certs_temp.sh"
                cat > $CERT_SCRIPT << EOSCRIPT
#!/bin/bash
CERT_LOCATIONS=(
    "/usr/local/etc/certificate"
    "/usr/syno/etc/certificate"
    "/usr/syno/etc/certificate/system/default"
    "/volume1/@appstore/CertManager/etc"
    "/etc/letsencrypt/live"
    "/usr/local/etc/letsencrypt/live"
    "/volume1/docker/letsencrypt/etc/live"
)

echo "Searching for certificate files for $DDNS_HOSTNAME..."
CERT_FOUND=false
mkdir -p "$DATA_DIR/ssl"

# First, search for directories with exact hostname match
echo "Search method 1: Looking for directories matching hostname..."
for LOC in "\${CERT_LOCATIONS[@]}"; do
    if [ -d "\$LOC" ]; then
        echo "Checking \$LOC..."
        if [ -d "\$LOC/$DDNS_HOSTNAME" ]; then
            if [ -f "\$LOC/$DDNS_HOSTNAME/fullchain.pem" ] && [ -f "\$LOC/$DDNS_HOSTNAME/privkey.pem" ]; then
                echo "Found certificates in \$LOC/$DDNS_HOSTNAME"
                cp "\$LOC/$DDNS_HOSTNAME/fullchain.pem" "$DATA_DIR/ssl/fullchain.pem"
                cp "\$LOC/$DDNS_HOSTNAME/privkey.pem" "$DATA_DIR/ssl/privkey.pem"
                chmod 644 "$DATA_DIR/ssl/fullchain.pem"
                chmod 600 "$DATA_DIR/ssl/privkey.pem"
                CERT_FOUND=true
                break
            fi
        fi
    fi
done

# Second, check for certificate files directly in known locations
if [ "\$CERT_FOUND" = false ]; then
    echo "Search method 2: Looking for certificate files directly..."
    for LOC in "\${CERT_LOCATIONS[@]}"; do
        if [ -d "\$LOC" ] && [ -f "\$LOC/fullchain.pem" ] && [ -f "\$LOC/privkey.pem" ]; then
            echo "Found certificates directly in \$LOC"
            cp "\$LOC/fullchain.pem" "$DATA_DIR/ssl/fullchain.pem"
            cp "\$LOC/privkey.pem" "$DATA_DIR/ssl/privkey.pem"
            chmod 644 "$DATA_DIR/ssl/fullchain.pem"
            chmod 600 "$DATA_DIR/ssl/privkey.pem"
            CERT_FOUND=true
            break
        fi
    done
fi

# Third, recursively search for certificates containing our domain name
if [ "\$CERT_FOUND" = false ]; then
    echo "Search method 3: Recursively searching for certificates by content..."
    for LOC in "\${CERT_LOCATIONS[@]}"; do
        if [ -d "\$LOC" ]; then
            # Find all certificate files recursively (depth limit to avoid long searches)
            FOUND_CERTS=\$(find "\$LOC" -maxdepth 3 -type f -name "fullchain.pem" 2>/dev/null)
            for CERT in \$FOUND_CERTS; do
                CERT_DIR=\$(dirname "\$CERT")
                if [ -f "\$CERT_DIR/privkey.pem" ]; then
                    # Check if certificate contains our domain
                    if openssl x509 -in "\$CERT" -noout -text | grep -q "\$DDNS_HOSTNAME"; then
                        echo "Found matching certificate in \$CERT_DIR"
                        cp "\$CERT" "$DATA_DIR/ssl/fullchain.pem"
                        cp "\$CERT_DIR/privkey.pem" "$DATA_DIR/ssl/privkey.pem"
                        chmod 644 "$DATA_DIR/ssl/fullchain.pem"
                        chmod 600 "$DATA_DIR/ssl/privkey.pem"
                        CERT_FOUND=true
                        break 2
                    fi
                fi
            done
        fi
    done
fi

if [ "\$CERT_FOUND" = true ]; then
    echo "Certificates copied to $DATA_DIR/ssl/"
    echo "Certificate details:"
    openssl x509 -in "$DATA_DIR/ssl/fullchain.pem" -noout -subject -issuer -dates
    exit 0
else
    echo "No certificates found for $DDNS_HOSTNAME"
    exit 1
fi
EOSCRIPT
                chmod +x $CERT_SCRIPT
                
                # Execute directly without sudo if possible, or use sh to execute it
                if [ "$EUID" -eq 0 ]; then
                    # Already running as root
                    if $CERT_SCRIPT; then
                        echo -e "${GREEN}✓ Certificates located and copied successfully${NC}"
                    else
                        echo -e "${RED}Error: Could not locate certificates${NC}"
                        echo "Generating self-signed certificate as fallback..."
                        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                            -keyout "$DATA_DIR/ssl/privkey.pem" \
                            -out "$DATA_DIR/ssl/fullchain.pem" \
                            -subj "/CN=$DDNS_HOSTNAME" \
                            -addext "subjectAltName=DNS:$DDNS_HOSTNAME,DNS:localhost"
                    fi
                else
                    # Try with sh instead of sudo
                    echo "Attempting to execute script with sh..."
                    if sh $CERT_SCRIPT; then
                        echo -e "${GREEN}✓ Certificates located and copied successfully${NC}"
                    else
                        echo -e "${RED}Error: Could not locate certificates${NC}"
                        echo "Generating self-signed certificate as fallback..."
                        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                            -keyout "$DATA_DIR/ssl/privkey.pem" \
                            -out "$DATA_DIR/ssl/fullchain.pem" \
                            -subj "/CN=$DDNS_HOSTNAME" \
                            -addext "subjectAltName=DNS:$DDNS_HOSTNAME,DNS:localhost"
                    fi
                fi
                
                # Clean up
                rm $CERT_SCRIPT
            fi
            ;;
        3)
            echo -e "${BOLD}Setting up Let's Encrypt certificate...${NC}"
            if [ "$IS_SYNOLOGY" = true ]; then
                # Create script in current directory instead of /tmp
                LE_SCRIPT="./letsencrypt_temp.sh"
                cat > $LE_SCRIPT << EOSCRIPT
#!/bin/bash
echo "Requesting Let's Encrypt certificate for $DDNS_HOSTNAME..."

if command -v synocertificate &> /dev/null; then
    synocertificate --apply-lets-encrypt \
        --domain "$DDNS_HOSTNAME" \
        --email "$DDNS_USERNAME" \
        --renew-auto true
    
    echo "Certificate request initiated. This might take a few minutes..."
    sleep 30
    
    for LOC in "/usr/local/etc/certificate" "/usr/syno/etc/certificate" "/usr/syno/etc/certificate/system/default"; do
        if [ -d "\$LOC" ] && [ -d "\$LOC/$DDNS_HOSTNAME" ]; then
            if [ -f "\$LOC/$DDNS_HOSTNAME/fullchain.pem" ] && [ -f "\$LOC/$DDNS_HOSTNAME/privkey.pem" ]; then
                echo "Found newly generated certificates in \$LOC/$DDNS_HOSTNAME"
                cp "\$LOC/$DDNS_HOSTNAME/fullchain.pem" "$DATA_DIR/ssl/fullchain.pem"
                cp "\$LOC/$DDNS_HOSTNAME/privkey.pem" "$DATA_DIR/ssl/privkey.pem"
                chmod 644 "$DATA_DIR/ssl/fullchain.pem"
                chmod 600 "$DATA_DIR/ssl/privkey.pem"
                CERT_FOUND=true
                break
            fi
        fi
    done
    
    if [ "\$CERT_FOUND" = true ]; then
        echo "Let's Encrypt certificate generated and copied successfully"
    else
        echo "Certificate requested, but files not found yet. They will be generated in background."
        echo "You may need to manually copy them later from DSM Certificate Manager"
    fi
else
    echo "Automated Let's Encrypt certificate request not available"
    echo "Please request the certificate manually through DSM:"
    echo "1. Go to Control Panel → Security → Certificate"
    echo "2. Click 'Add' and select 'Add a new certificate'"
    echo "3. Choose 'Get a certificate from Let's Encrypt'"
    echo "4. Enter '$DDNS_HOSTNAME' as the domain name"
    echo "5. Complete the wizard"
fi
EOSCRIPT
                chmod +x $LE_SCRIPT
                
                # Execute directly without sudo if possible, or use sh to execute it
                if [ "$EUID" -eq 0 ]; then
                    # Already running as root
                    $LE_SCRIPT
                else
                    # Try with sh instead of sudo
                    echo "Attempting to execute script with sh..."
                    sh $LE_SCRIPT
                fi
                
                # Clean up
                rm $LE_SCRIPT
            fi
            ;;
        4)
            echo "Skipping certificate setup. Using existing certificates if available."
            ;;
    esac
fi

# Create necessary directories with proper permissions
echo -e "${BOLD}Creating necessary directories and setting permissions...${NC}"
mkdir -p "$DATA_DIR"
mkdir -p "$DATA_DIR/instance"
mkdir -p "$DATA_DIR/templates"
mkdir -p "$DATA_DIR/static/css"
mkdir -p "$DATA_DIR/static/js"
mkdir -p "$DATA_DIR/ssl"
mkdir -p "$DATA_DIR/nginx/conf.d"
chmod -R 777 "$DATA_DIR"  # Ensure database directory is writable
touch "$DATA_DIR/app.db"  # Create empty database file
chmod 666 "$DATA_DIR/app.db"  # Make database file writable
echo -e "${GREEN}✓ Directories and permissions set${NC}"
echo

# Copy web templates and static files
echo -e "${BOLD}Setting up web interface...${NC}"

# Copy template files if they exist
if [ -d "./server/templates" ]; then
    echo "Copying template files..."
    cp -r ./server/templates/* "$DATA_DIR/templates/"
    echo -e "${GREEN}✓ Template files copied${NC}"
else
    echo -e "${YELLOW}Template directory not found, creating default templates...${NC}"
    
    # Create base template
    cat > "$DATA_DIR/templates/base.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AMRS Maintenance Tracker{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    {% block head %}{% endblock %}
</head>
<body>
    <header>
        <div class="logo">
            <h1>AMRS Maintenance Tracker</h1>
        </div>
        <nav>
            <ul>
                <li><a href="{{ url_for('index') }}" {% if request.endpoint == 'index' %}class="active"{% endif %}>Dashboard</a></li>
                <li><a href="{{ url_for('maintenance') }}" {% if request.endpoint == 'maintenance' %}class="active"{% endif %}>Maintenance</a></li>
                {% if current_user %}
                <li><a href="{{ url_for('logout') }}">Logout</a></li>
                {% endif %}
            </ul>
        </nav>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; 2023 AMRS Maintenance Tracker</p>
    </footer>

    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
EOF

    # Create login template
    cat > "$DATA_DIR/templates/login.html" << 'EOF'
{% extends "base.html" %}

{% block title %}Login - AMRS Maintenance Tracker{% endblock %}

{% block content %}
<div class="auth-container">
    <div class="auth-form">
        <h2>Login</h2>
        {% if error %}
        <div class="error-message">
            {{ error }}
        </div>
        {% endif %}
        <form method="post" action="{{ url_for('login') }}">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <div class="form-group remember-me">
                <input type="checkbox" id="remember" name="remember">
                <label for="remember">Remember me</label>
            </div>
            <button type="submit" class="btn-primary">Login</button>
        </form>
    </div>
</div>
{% endblock %}
EOF

    # Create index template
    cat > "$DATA_DIR/templates/index.html" << 'EOF'
{% extends "base.html" %}

{% block title %}Dashboard - AMRS Maintenance Tracker{% endblock %}

{% block content %}
<div class="dashboard">
    <h2>Maintenance Dashboard</h2>
    
    <div class="stats-container">
        <div class="stat-card overdue">
            <div class="stat-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="stat-content">
                <h3>Overdue</h3>
                <p class="stat-value">{{ dashboard.overdue_count }}</p>
            </div>
        </div>
        
        <div class="stat-card due-soon">
            <div class="stat-icon">
                <i class="fas fa-clock"></i>
            </div>
            <div class="stat-content">
                <h3>Due Soon</h3>
                <p class="stat-value">{{ dashboard.due_soon_count }}</p>
            </div>
        </div>
        
        <div class="stat-card total-parts">
            <div class="stat-icon">
                <i class="fas fa-cogs"></i>
            </div>
            <div class="stat-content">
                <h3>Total Parts</h3>
                <p class="stat-value">{{ dashboard.total_parts }}</p>
            </div>
        </div>
    </div>
    
    <div class="recent-maintenance">
        <h3>Recent Maintenance Activities</h3>
        {% if recent_maintenance %}
        <table class="data-table">
            <thead>
                <tr>
                    <th>Part</th>
                    <th>Machine</th>
                    <th>Site</th>
                    <th>Date</th>
                    <th>Technician</th>
                </tr>
            </thead>
            <tbody>
                {% for record in recent_maintenance %}
                <tr>
                    <td>{{ record.part_name }}</td>
                    <td>{{ record.machine_name }}</td>
                    <td>{{ record.site_name }}</td>
                    <td>{{ record.date }}</td>
                    <td>{{ record.technician }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p class="no-data">No recent maintenance records found.</p>
        {% endif %}
    </div>
</div>
{% endblock %}
EOF

    # Create maintenance template
    cat > "$DATA_DIR/templates/maintenance.html" << 'EOF'
{% extends "base.html" %}

{% block title %}Maintenance - AMRS Maintenance Tracker{% endblock %}

{% block content %}
<div class="maintenance-page">
    <h2>Maintenance Checklist</h2>
    
    <div class="filter-controls">
        <div class="filter-group">
            <label for="site-filter">Site:</label>
            <select id="site-filter" class="filter-select">
                <option value="-1">All Sites</option>
                {% for site in sites %}
                <option value="{{ site.id }}">{{ site.name }}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="filter-group">
            <label for="machine-filter">Machine:</label>
            <select id="machine-filter" class="filter-select">
                <option value="-1">All Machines</option>
            </select>
        </div>
        
        <div class="status-filters">
            <label>
                <input type="checkbox" class="status-checkbox" data-status="overdue" checked>
                Overdue
            </label>
            <label>
                <input type="checkbox" class="status-checkbox" data-status="due_soon" checked>
                Due Soon
            </label>
            <label>
                <input type="checkbox" class="status-checkbox" data-status="ok">
                Ok
            </label>
        </div>
    </div>
    
    <div class="parts-table-container">
        <table id="parts-table" class="data-table">
            <thead>
                <tr>
                    <th>Part</th>
                    <th>Machine</th>
                    <th>Site</th>
                    <th>Last Maintenance</th>
                    <th>Next Due</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                <!-- Will be populated by JavaScript -->
            </tbody>
        </table>
    </div>
    
    <!-- Maintenance Record Modal -->
    <div id="maintenance-modal" class="modal">
        <div class="modal-content">
            <span class="close-button">&times;</span>
            <h3>Record Maintenance</h3>
            <form id="maintenance-form">
                <input type="hidden" id="part-id">
                <div class="form-group">
                    <label>Part: <span id="part-name"></span></label>
                </div>
                <div class="form-group">
                    <label for="maintenance-notes">Notes:</label>
                    <textarea id="maintenance-notes" rows="4" placeholder="Enter maintenance details..."></textarea>
                </div>
                <button type="submit" class="btn-primary">Record Maintenance</button>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // Load sites and parts data on page load
        loadSites();
        loadParts();
        
        // Event listeners
        document.getElementById('site-filter').addEventListener('change', function() {
            loadMachinesForSite(this.value);
            loadParts();
        });
        
        document.getElementById('machine-filter').addEventListener('change', loadParts);
        
        document.querySelectorAll('.status-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', loadParts);
        });
        
        // Modal setup
        const modal = document.getElementById('maintenance-modal');
        const closeBtn = document.querySelector('.close-button');
        closeBtn.addEventListener('click', () => modal.style.display = 'none');
        
        // Form submission
        document.getElementById('maintenance-form').addEventListener('submit', recordMaintenance);
    });
</script>
{% endblock %}
EOF

    # Create 404 template
    cat > "$DATA_DIR/templates/404.html" << 'EOF'
{% extends "base.html" %}

{% block title %}Page Not Found - AMRS Maintenance Tracker{% endblock %}

{% block content %}
<div class="error-page">
    <h2>404 - Page Not Found</h2>
    <p>The page you're looking for doesn't exist.</p>
    <p><a href="{{ url_for('index') }}">Return to Dashboard</a></p>
</div>
{% endblock %}
EOF
    echo -e "${GREEN}✓ Default templates created${NC}"
fi

# Copy CSS files
if [ -d "./server/static/css" ]; then
    echo "Copying CSS files..."
    cp -r ./server/static/css/* "$DATA_DIR/static/css/"
    echo -e "${GREEN}✓ CSS files copied${NC}"
else
    echo -e "${YELLOW}CSS directory not found, creating main stylesheet...${NC}"
    # Create minimal CSS
    cat > "$DATA_DIR/static/css/style.css" << 'EOF'
/* Main Styles for AMRS Maintenance Tracker */
:root {
    --primary: #3498db;
    --secondary: #2980b9;
    --accent: #27ae60;
    --danger: #e74c3c;
    --warning: #f1c40f;
    --light: #ecf0f1;
    --dark: #34495e;
    --text: #333333;
    --text-light: #666666;
    --background: #f8f9fa;
    --card-bg: #ffffff;
    --border: #dddddd;
}

/* Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: var(--background);
    color: var(--text);
    line-height: 1.6;
}

a {
    text-decoration: none;
    color: var(--primary);
}

a:hover {
    color: var(--secondary);
}

/* Header */
header {
    background-color: var(--card-bg);
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo h1 {
    font-size: 1.5rem;
    color: var(--primary);
}

nav ul {
    display: flex;
    list-style: none;
}

nav ul li {
    margin-left: 1.5rem;
}

nav ul li a {
    color: var(--dark);
    font-weight: 500;
    padding: 0.5rem;
}

nav ul li a.active {
    color: var(--primary);
    border-bottom: 2px solid var(--primary);
}

/* Main Content */
main {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 1.5rem;
}

h2 {
    color: var(--dark);
    margin-bottom: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}

/* Dashboard Stats */
.stats-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stat-card {
    background-color: var(--card-bg);
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
}

.stat-icon {
    font-size: 2.5rem;
    margin-right: 1rem;
}

.stat-content h3 {
    font-size: 1rem;
    color: var(--text-light);
    margin-bottom: 0.25rem;
}

.stat-value {
    font-size: 2rem;
    font-weight: bold;
}

.overdue .stat-icon {
    color: var(--danger);
}

.due-soon .stat-icon {
    color: var(--warning);
}

.total-parts .stat-icon {
    color: var(--accent);
}

/* Tables */
.data-table {
    width: 100%;
    border-collapse: collapse;
    background-color: var(--card-bg);
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    margin-top: 1rem;
}

.data-table th, .data-table td {
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
}

.data-table th {
    background-color: var(--light);
    font-weight: 600;
}

.data-table tr:hover {
    background-color: rgba(52, 152, 219, 0.05);
}

/* Forms and Authentication */
.auth-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - 200px);
}

.auth-form {
    background-color: var(--card-bg);
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
}

.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
}

.form-group input, .form-group textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--border);
    border-radius: 4px;
}

button, .btn-primary {
    background-color: var(--primary);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
}

button:hover, .btn-primary:hover {
    background-color: var(--secondary);
}

.error-message {
    background-color: rgba(231, 76, 60, 0.1);
    border-left: 4px solid var(--danger);
    padding: 0.75rem 1rem;
    margin-bottom: 1rem;
    color: var(--danger);
}

/* Modal */
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
}

.modal-content {
    background-color: var(--card-bg);
    margin: 10% auto;
    padding: 2rem;
    width: 50%;
    max-width: 500px;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    position: relative;
}

.close-button {
    position: absolute;
    right: 1rem;
    top: 1rem;
    font-size: 1.5rem;
    cursor: pointer;
}

/* Footer */
footer {
    background-color: var(--dark);
    color: var(--light);
    text-align: center;
    padding: 1.5rem;
    margin-top: 2rem;
}
EOF
    echo -e "${GREEN}✓ Default stylesheet created${NC}"
fi

# Copy JavaScript files
if [ -d "./server/static/js" ]; then
    echo "Copying JavaScript files..."
    cp -r ./server/static/js/* "$DATA_DIR/static/js/"
    echo -e "${GREEN}✓ JavaScript files copied${NC}"
else
    echo -e "${YELLOW}JavaScript directory not found, creating main script...${NC}"
    # Create minimal JavaScript
    cat > "$DATA_DIR/static/js/main.js" << 'EOF'
// Main JavaScript for AMRS Maintenance Tracker

// Helper function for API calls
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const headers = {
            'Content-Type': 'application/json',
        };
        
        // Get auth token from local storage if available
        const authToken = localStorage.getItem('auth_token');
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const options = {
            method,
            headers,
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Load parts with filters
async function loadParts() {
    const siteFilter = document.getElementById('site-filter');
    const machineFilter = document.getElementById('machine-filter');
    
    if (!siteFilter || !machineFilter) return; // Not on the maintenance page
    
    const siteId = siteFilter.value;
    const machineId = machineFilter.value;
    
    // Build query string for filters
    let queryParams = [];
    if (siteId && siteId != -1) queryParams.push(`site_id=${siteId}`);
    if (machineId && machineId != -1) queryParams.push(`machine_id=${machineId}`);
    
    // Add status filters if they exist
    const statusCheckboxes = document.querySelectorAll('.status-checkbox');
    if (statusCheckboxes.length > 0) {
        const statuses = [];
        statusCheckboxes.forEach(cb => {
            if (cb.checked) statuses.push(cb.dataset.status);
        });
        if (statuses.length > 0 && statuses.length < statusCheckboxes.length) {
            queryParams.push(`status=${statuses.join(',')}`);
        }
    }
    
    const queryString = queryParams.length ? `?${queryParams.join('&')}` : '';
    
    try {
        const data = await apiCall(`/api/parts${queryString}`);
        const parts = data.parts || [];
        
        // Update table with parts data
        const table = document.getElementById('parts-table');
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        tbody.innerHTML = '';
        
        if (parts.length === 0) {
            const row = tbody.insertRow();
            const cell = row.insertCell(0);
            cell.colSpan = 7;
            cell.textContent = 'No parts match your filter criteria.';
            cell.style.textAlign = 'center';
            cell.style.padding = '2rem 0';
            return;
        }
        
        parts.forEach(part => {
            const row = tbody.insertRow();
            
            row.insertCell(0).textContent = part.name;
            row.insertCell(1).textContent = part.machine_name;
            row.insertCell(2).textContent = part.site_name;
            row.insertCell(3).textContent = part.last_maintenance || 'Never';
            row.insertCell(4).textContent = part.next_due || 'Unknown';
            
            const statusCell = row.insertCell(5);
            const statusSpan = document.createElement('span');
            statusSpan.className = `status status-${part.status}`;
            statusSpan.textContent = part.status === 'due_soon' ? 'Due Soon' : 
                                    (part.status === 'overdue' ? 'Overdue' : 'OK');
            statusCell.appendChild(statusSpan);
            
            const actionsCell = row.insertCell(6);
            const recordButton = document.createElement('button');
            recordButton.textContent = 'Record';
            recordButton.className = 'btn-primary';
            recordButton.onclick = () => showMaintenanceModal(part);
            actionsCell.appendChild(recordButton);
            
            // Double-click to record maintenance
            row.ondblclick = () => showMaintenanceModal(part);
        });
    } catch (error) {
        console.error('Error loading parts:', error);
        alert('Failed to load parts. Please try again later.');
    }
}

// Load machines for a site
async function loadMachinesForSite(siteId) {
    const machineFilter = document.getElementById('machine-filter');
    if (!machineFilter) return;
    
    machineFilter.innerHTML = '<option value="-1">All Machines</option>';
    
    if (siteId == -1) return;
    
    try {
        const data = await apiCall(`/api/machines?site_id=${siteId}`);
        const machines = data.machines || [];
        
        machines.forEach(machine => {
            const option = document.createElement('option');
            option.value = machine.id;
            option.textContent = machine.name;
            machineFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading machines:', error);
    }
}

// Load available sites
async function loadSites() {
    const siteFilter = document.getElementById('site-filter');
    if (!siteFilter) return;
    
    try {
        const data = await apiCall('/api/sites');
        const sites = data.sites || [];
        
        siteFilter.innerHTML = '<option value="-1">All Sites</option>';
        sites.forEach(site => {
            const option = document.createElement('option');
            option.value = site.id;
            option.textContent = site.name;
            siteFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading sites:', error);
    }
}

// Show maintenance modal
function showMaintenanceModal(part) {
    const modal = document.getElementById('maintenance-modal');
    if (!modal) return;
    
    document.getElementById('part-id').value = part.id;
    document.getElementById('part-name').textContent = part.name;
    document.getElementById('maintenance-notes').value = '';
    
    modal.style.display = 'block';
}

// Record maintenance
async function recordMaintenance(event) {
    event.preventDefault();
    
    const partId = document.getElementById('part-id').value;
    const notes = document.getElementById('maintenance-notes').value;
    
    try {
        const response = await apiCall('/api/maintenance/record', 'POST', {
            part_id: partId,
            notes: notes
        });
        
        if (response.status === 'success') {
            document.getElementById('maintenance-modal').style.display = 'none';
            alert('Maintenance recorded successfully!');
            loadParts(); // Refresh parts list
        }
    } catch (error) {
        console.error('Error recording maintenance:', error);
        alert('Failed to record maintenance. Please try again.');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Initialize maintenance page functionality if applicable
    if (document.querySelector('.maintenance-page')) {
        loadSites();
        loadParts();
    }
});
EOF
    echo -e "${GREEN}✓ Default JavaScript created${NC}"
fi

# Create docker-compose.yml
echo -e "${BOLD}Creating Docker Compose configuration...${NC}"
cat > docker-compose.yml << EOL
version: '3'

services:
  app:
    build: ./server
    ports:
      - "$CONTAINER_PORT:$CONTAINER_PORT"
    environment:
      - DATABASE_URL=sqlite:////app/data/app.db
      - SECRET_KEY=secure_$(date +%s)_key
      - DEBUG=False
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - SERVER_NAME=$DDNS_HOSTNAME
      - PREFERRED_URL_SCHEME=https
    volumes:
      - $DATA_DIR:/app/data
    restart: "unless-stopped"
    container_name: amrs-maintenance-tracker
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:$CONTAINER_PORT/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  nginx:
    image: nginx:alpine
    ports:
      - "$EXTERNAL_PORT_HTTP:80"
      - "$EXTERNAL_PORT_HTTPS:443"
    volumes:
      - $DATA_DIR/nginx/conf.d:/etc/nginx/conf.d
      - $DATA_DIR/ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
EOL
echo -e "${GREEN}✓ Docker Compose file created${NC}"
echo

# Create Nginx configuration
echo -e "${BOLD}Creating Nginx configuration...${NC}"
cat > "$DATA_DIR/nginx/conf.d/default.conf" << EOL
server {
    listen 80;
    server_name $DDNS_HOSTNAME;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DDNS_HOSTNAME;
    
    # SSL certificates
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL optimizations
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    
    # Modern TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy requests to the Flask app
    location / {
        proxy_pass http://app:$CONTAINER_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL
echo -e "${GREEN}✓ Nginx configuration created${NC}"
echo

# Create DSM Reverse Proxy guide
echo -e "${BOLD}Creating Synology reverse proxy guide...${NC}"
cat > reverse_proxy_guide.txt << EOL
Synology Reverse Proxy Configuration Guide
=========================================

Two configuration options are available:

Option 1: Using Nginx Docker Container (current setup)
----------------------------------------------------
The docker-compose.yml is already configured for this approach.
Just follow the router port forwarding instructions at the end of this setup.

Option 2: Using Synology's Built-in Reverse Proxy
------------------------------------------------
If you prefer to use Synology's reverse proxy instead of the Nginx container:

1. Go to DSM Control Panel → Login Portal → Advanced → Reverse Proxy
2. Click "Create" and set up:
   - Source:
     - Protocol: HTTPS
     - Hostname: $DDNS_HOSTNAME
     - Port: 443 (default HTTPS port)
   - Destination:
     - Protocol: HTTP
     - Hostname: localhost
     - Port: $CONTAINER_PORT

3. Click "OK" to save

4. Modify docker-compose.yml to remove the nginx service and use:
   docker-compose up -d app
EOL
echo -e "${GREEN}✓ Synology reverse proxy guide created${NC}"
echo

# Start the containers
echo -e "${BOLD}Starting Docker containers...${NC}"
docker-compose build --no-cache app
docker-compose up -d
echo -e "${GREEN}✓ Docker containers started${NC}"
echo

# Generate Windows client configuration
if [ -d "./windows_client" ]; then
    echo -e "${BOLD}Creating pre-configured Windows client...${NC}"
    cat > ./windows_client/server_config.json << EOL
{
    "server_url": "https://$DDNS_HOSTNAME",
    "preconfigured": true
}
EOL
    echo -e "${GREEN}✓ Windows client configuration created${NC}"
    echo
fi

# Output URLs and next steps
echo -e "${BOLD}${GREEN}Setup completed successfully!${NC}"
echo
echo -e "${BOLD}URLs:${NC}"
echo "  Local API: http://$SYNOLOGY_IP:$CONTAINER_PORT/api"
echo "  Local Web Interface: http://$SYNOLOGY_IP:$CONTAINER_PORT"
echo "  Local with Nginx: https://$SYNOLOGY_IP:$EXTERNAL_PORT_HTTPS"
echo "  External URL (after router setup): https://$DDNS_HOSTNAME"
echo
echo -e "${BOLD}${YELLOW}Final Steps:${NC}"
echo "1. Configure your router to forward the following ports to your Synology ($SYNOLOGY_IP):"
echo "   - Forward external port 80 to internal port $EXTERNAL_PORT_HTTP (HTTP)"
echo "   - Forward external port 443 to internal port $EXTERNAL_PORT_HTTPS (HTTPS)"
echo
echo "2. Set up DDNS in your Synology:"
echo "   - Go to Control Panel → External Access → DDNS"
echo "   - Configure your DDNS provider with hostname: $DDNS_HOSTNAME"
echo
echo "3. For production use, replace the temporary SSL certificates:"
echo "   - Use Synology's Let's Encrypt integration in Control Panel → Security → Certificate"
echo "   - Copy the certificate files to $DATA_DIR/ssl/ (fullchain.pem and privkey.pem)"
echo "   - Or obtain your own certificates and place them in the same location"
echo
echo "4. Build Windows client (optional):"
if [ -d "./windows_client" ]; then
    echo "   - cd windows_client"
    echo "   - python build.py --server-url https://$DDNS_HOSTNAME"
fi
echo
echo -e "${BOLD}${GREEN}Access Options:${NC}"
echo "1. Web Interface: https://$DDNS_HOSTNAME"
echo "   - Username: admin"
echo "   - Password: admin"
echo
echo "2. Windows Client: Use the pre-configured Windows client"
echo
echo "3. API Direct Access: https://$DDNS_HOSTNAME/api"
echo
echo "Detailed reverse proxy information saved to reverse_proxy_guide.txt"
echo -e "${BOLD}${GREEN}Enjoy your AMRS Preventative Maintenance system!${NC}"
