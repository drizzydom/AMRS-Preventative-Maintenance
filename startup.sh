#!/bin/bash
# Startup script for ensuring database is ready before starting the app

echo "[STARTUP] Starting application setup..."

# Create data directory if it doesn't exist
if [ ! -d "/var/data" ]; then
    echo "[STARTUP] Creating /var/data directory..."
    mkdir -p /var/data || echo "[ERROR] Failed to create /var/data directory"
fi

# Set proper permissions
echo "[STARTUP] Setting permissions on data directory..."
chmod -R 755 /var/data || echo "[ERROR] Failed to set permissions on /var/data"

# Create backups directory if it doesn't exist
echo "[STARTUP] Creating backups directory..."
mkdir -p /var/data/backups || echo "[ERROR] Failed to create backups directory"
chmod -R 755 /var/data/backups || echo "[ERROR] Failed to set permissions on backups directory"

# List contents of data directory
echo "[STARTUP] Data directory contents:"
ls -la /var/data || echo "[ERROR] Failed to list /var/data contents"

# Print environment diagnostics
echo "[STARTUP] Environment diagnostics:"
echo "  FLASK_APP: $FLASK_APP"
echo "  SERVER_NAME: $SERVER_NAME"
echo "  APPLICATION_ROOT: $APPLICATION_ROOT"
echo "  PYTHONPATH: $PYTHONPATH"
echo "  Working directory: $(pwd)"

# Create error templates directory if it doesn't exist
echo "[STARTUP] Creating error templates directory..."
mkdir -p templates/errors
if [ ! -f "templates/errors/404.html" ]; then
    echo "[STARTUP] Creating 404 error template..."
    cat > templates/errors/404.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Page Not Found</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { color: #FE7900; }
        a { color: #FE7900; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Page Not Found</h1>
    <p>The requested page was not found. Please check the URL or go back to the <a href="/">home page</a>.</p>
</body>
</html>
EOF
fi

if [ ! -f "templates/errors/500.html" ]; then
    echo "[STARTUP] Creating 500 error template..."
    cat > templates/errors/500.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Server Error</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { color: #FE7900; }
        a { color: #FE7900; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Server Error</h1>
    <p>Sorry, something went wrong on our end. Please try again later or go back to the <a href="/">home page</a>.</p>
</body>
</html>
EOF
fi

echo "[STARTUP] Starting application server..."
# Start the application with more verbose logging and log access
exec gunicorn app:app --log-level debug --access-logfile - --error-logfile - --capture-output --bind 0.0.0.0:$PORT
