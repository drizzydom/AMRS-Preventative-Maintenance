#!/bin/bash
# =============================================================================
# AMRS Template Setup Script
# This script sets up basic template files for the application
# =============================================================================

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}AMRS Template Setup Script${NC}"
echo "=========================="
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

# Create template directories
TEMPLATES_DIR="$DATA_DIR/templates"
STATIC_DIR="$DATA_DIR/static"
mkdir -p "$TEMPLATES_DIR"
mkdir -p "$STATIC_DIR/css"
mkdir -p "$STATIC_DIR/js"

echo -e "${BOLD}1. Creating base template...${NC}"
cat > "$TEMPLATES_DIR/base.html" << 'EOL'
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
                {% if session.get('user_id') %}
                    <li><a href="{{ url_for('index') }}" {% if request.endpoint == 'index' %}class="active"{% endif %}>Dashboard</a></li>
                    <li><a href="{{ url_for('maintenance') }}" {% if request.endpoint == 'maintenance' %}class="active"{% endif %}>Maintenance</a></li>
                    <li><a href="{{ url_for('logout') }}">Logout ({{ session.get('username') }})</a></li>
                {% else %}
                    <li><a href="{{ url_for('login') }}" {% if request.endpoint == 'login' %}class="active"{% endif %}>Login</a></li>
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
EOL
echo -e "${GREEN}✓ Base template created${NC}"

echo -e "${BOLD}2. Creating index template...${NC}"
cat > "$TEMPLATES_DIR/index.html" << 'EOL'
{% extends "base.html" %}

{% block title %}Dashboard - AMRS Maintenance Tracker{% endblock %}

{% block content %}
<div class="dashboard">
    <h2>Maintenance Dashboard</h2>
    
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-content">
                <h3>Overdue</h3>
                <p class="stat-value">{{ dashboard.overdue_count|default(0) }}</p>
            </div>
        </div>
        
        <div class="stat-card">
            <div class="stat-content">
                <h3>Due Soon</h3>
                <p class="stat-value">{{ dashboard.due_soon_count|default(0) }}</p>
            </div>
        </div>
        
        <div class="stat-card">
            <div class="stat-content">
                <h3>Total Parts</h3>
                <p class="stat-value">{{ dashboard.total_parts|default(0) }}</p>
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
        <p>No recent maintenance records found.</p>
        {% endif %}
    </div>
</div>
{% endblock %}
EOL
echo -e "${GREEN}✓ Index template created${NC}"

echo -e "${BOLD}3. Creating login template...${NC}"
cat > "$TEMPLATES_DIR/login.html" << 'EOL'
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
EOL
echo -e "${GREEN}✓ Login template created${NC}"

echo -e "${BOLD}4. Creating error templates...${NC}"
cat > "$TEMPLATES_DIR/404.html" << 'EOL'
{% extends "base.html" %}

{% block title %}Page Not Found - AMRS Maintenance Tracker{% endblock %}

{% block content %}
<div class="error-page">
    <h2>404 - Page Not Found</h2>
    <p>The page you're looking for doesn't exist or has been moved.</p>
    <p><a href="{{ url_for('index') }}" class="btn-primary">Return to Dashboard</a></p>
</div>
{% endblock %}
EOL

cat > "$TEMPLATES_DIR/500.html" << 'EOL'
{% extends "base.html" %}

{% block title %}Server Error - AMRS Maintenance Tracker{% endblock %}

{% block content %}
<div class="error-page">
    <h2>500 - Internal Server Error</h2>
    <p>Something went wrong on our end. Please try again later.</p>
    <p><a href="{{ url_for('index') }}" class="btn-primary">Return to Dashboard</a></p>
</div>
{% endblock %}
EOL
echo -e "${GREEN}✓ Error templates created${NC}"

echo -e "${BOLD}5. Creating CSS file...${NC}"
cat > "$STATIC_DIR/css/style.css" << 'EOL'
/* Basic styling for AMRS Maintenance Tracker */
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
}

.stat-content h3 {
    font-size: 1rem;
    color: var(--text-light);
    margin-bottom: 0.5rem;
}

.stat-value {
    font-size: 2rem;
    font-weight: bold;
    color: var(--primary);
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

/* Authentication */
.auth-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 70vh;
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

.form-group input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--border);
    border-radius: 4px;
}

.btn-primary {
    background-color: var(--primary);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: background-color 0.3s;
}

.btn-primary:hover {
    background-color: var(--secondary);
}

.remember-me {
    display: flex;
    align-items: center;
}

.remember-me input {
    width: auto;
    margin-right: 0.5rem;
}

.error-message {
    background-color: rgba(231, 76, 60, 0.1);
    border-left: 4px solid var(--danger);
    padding: 0.75rem 1rem;
    margin-bottom: 1rem;
    color: var(--danger);
}

.error-page {
    text-align: center;
    padding: 3rem 1rem;
}

/* Footer */
footer {
    text-align: center;
    padding: 1.5rem;
    margin-top: 2rem;
    color: var(--text-light);
    border-top: 1px solid var(--border);
}

/* Responsive */
@media (max-width: 768px) {
    header {
        flex-direction: column;
    }
    
    nav ul {
        margin-top: 1rem;
    }
    
    .stats-container {
        grid-template-columns: 1fr;
    }
}
EOL
echo -e "${GREEN}✓ CSS file created${NC}"

echo -e "${BOLD}6. Creating JavaScript file...${NC}"
cat > "$STATIC_DIR/js/main.js" << 'EOL'
// Main JavaScript for AMRS Maintenance Tracker
document.addEventListener('DOMContentLoaded', function() {
    console.log('AMRS Maintenance Tracker initialized');
    
    // Add fade-in animation to main content
    const main = document.querySelector('main');
    if (main) {
        main.style.opacity = '0';
        main.style.transition = 'opacity 0.3s ease-in';
        setTimeout(() => {
            main.style.opacity = '1';
        }, 100);
    }
    
    // Handle form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerText = 'Processing...';
            }
        });
    });
    
    // Handle maintenance record filtering if on maintenance page
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        const filterInputs = filterForm.querySelectorAll('select, input');
        filterInputs.forEach(input => {
            input.addEventListener('change', function() {
                filterForm.submit();
            });
        });
    }
});
EOL
echo -e "${GREEN}✓ JavaScript file created${NC}"

echo
echo -e "${GREEN}${BOLD}Template setup completed!${NC}"
echo "All necessary template files have been created in $TEMPLATES_DIR"
echo "All necessary static files have been created in $STATIC_DIR"
