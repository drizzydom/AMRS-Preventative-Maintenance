#!/bin/bash
# =============================================================================
# AMRS Template Permissions Fix Script
# This script fixes permission issues with templates and static files
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Template Permissions Fix${NC}"
echo "============================="
echo

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

echo -e "${BOLD}1. Setting template directory permissions...${NC}"
mkdir -p "$DATA_DIR/templates"
chmod -R 777 "$DATA_DIR/templates"
echo -e "${GREEN}✓ Template directory permissions set to 777${NC}"

echo -e "${BOLD}2. Setting static directory permissions...${NC}"
mkdir -p "$DATA_DIR/static"
chmod -R 777 "$DATA_DIR/static"
echo -e "${GREEN}✓ Static directory permissions set to 777${NC}"

echo -e "${BOLD}3. Ensuring template files are accessible...${NC}"
if [ -d "$DATA_DIR/templates" ]; then
    find "$DATA_DIR/templates" -type f -exec chmod 666 {} \;
    echo -e "${GREEN}✓ Template file permissions set to 666${NC}"
else
    echo -e "${YELLOW}! No template directory found${NC}"
fi

echo -e "${BOLD}4. Running container as root temporarily...${NC}"
# Check if docker-compose file exists
DOCKER_COMPOSE_FILE="docker-compose.yml"
if [ -f "$DOCKER_COMPOSE_FILE" ]; then
    # Temporarily modify to use root user
    sed -i.bak 's/user: "1000:1000"/user: "root"/' "$DOCKER_COMPOSE_FILE" || true
    echo -e "${GREEN}✓ Modified docker-compose to use root user${NC}"
else
    echo -e "${YELLOW}! Docker compose file not found${NC}"
fi

echo -e "${BOLD}5. Restarting the app container...${NC}"
docker-compose stop app
docker-compose up -d app
echo -e "${GREEN}✓ App container restarted${NC}"

echo -e "${BOLD}6. Creating default template files if needed...${NC}"
# Create a basic set of template files if they don't exist
TEMPLATE_DIR="$DATA_DIR/templates"
mkdir -p "$TEMPLATE_DIR"

# Create base template if it doesn't exist
if [ ! -f "$TEMPLATE_DIR/base.html" ]; then
    cat > "$TEMPLATE_DIR/base.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AMRS Maintenance Tracker{% endblock %}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        header { background: #3498db; color: white; padding: 1rem; }
        main { padding: 1rem; }
        footer { text-align: center; padding: 1rem; border-top: 1px solid #eee; }
    </style>
    {% block head %}{% endblock %}
</head>
<body>
    <header>
        <h1>AMRS Maintenance Tracker</h1>
        <nav>
            {% if session.get('user_id') %}
                <a href="{{ url_for('index') }}">Dashboard</a>
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}">Login</a>
            {% endif %}
        </nav>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; 2023 AMRS Maintenance Tracker</p>
    </footer>
</body>
</html>
EOF
    chmod 666 "$TEMPLATE_DIR/base.html"
    echo -e "${GREEN}✓ Created base.html template${NC}"
fi

# Create login template
if [ ! -f "$TEMPLATE_DIR/login.html" ]; then
    cat > "$TEMPLATE_DIR/login.html" << 'EOF'
{% extends "base.html" %}

{% block title %}Login - AMRS{% endblock %}

{% block content %}
<h2>Login</h2>
{% if error %}
<p style="color: red;">{{ error }}</p>
{% endif %}
<form method="post">
    <div>
        <label>Username:</label>
        <input type="text" name="username" required>
    </div>
    <div>
        <label>Password:</label>
        <input type="password" name="password" required>
    </div>
    <div>
        <input type="checkbox" name="remember"> Remember me
    </div>
    <button type="submit">Login</button>
</form>
{% endblock %}
EOF
    chmod 666 "$TEMPLATE_DIR/login.html"
    echo -e "${GREEN}✓ Created login.html template${NC}"
fi

# Create index template
if [ ! -f "$TEMPLATE_DIR/index.html" ]; then
    cat > "$TEMPLATE_DIR/index.html" << 'EOF'
{% extends "base.html" %}

{% block title %}Dashboard - AMRS{% endblock %}

{% block content %}
<h2>Maintenance Dashboard</h2>
<p>Welcome to the AMRS Maintenance Tracker!</p>

<div>
    <h3>Maintenance Statistics</h3>
    <ul>
        <li>Total Parts: {{ dashboard.total_parts|default(0) }}</li>
        <li>Overdue: {{ dashboard.overdue_count|default(0) }}</li>
        <li>Due Soon: {{ dashboard.due_soon_count|default(0) }}</li>
    </ul>
</div>

<div>
    <h3>Recent Maintenance</h3>
    {% if recent_maintenance %}
    <table border="1">
        <tr>
            <th>Part</th>
            <th>Date</th>
            <th>Technician</th>
        </tr>
        {% for record in recent_maintenance %}
        <tr>
            <td>{{ record.part_name }}</td>
            <td>{{ record.date }}</td>
            <td>{{ record.technician }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No recent maintenance records found.</p>
    {% endif %}
</div>
{% endblock %}
EOF
    chmod 666 "$TEMPLATE_DIR/index.html"
    echo -e "${GREEN}✓ Created index.html template${NC}"
fi

echo
echo -e "${GREEN}${BOLD}Template permission fixes completed!${NC}"
echo "The app container has been restarted with root permissions"
echo "and template files have been created with appropriate permissions."
echo
echo "After verifying that the app works correctly, you should revert the"
echo "docker-compose.yml file to use the non-root user:"
echo
echo "sed -i.bak 's/user: \"root\"/user: \"1000:1000\"/' docker-compose.yml"
