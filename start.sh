#!/bin/bash
set -e

echo "Starting Render deployment script"

# Setup virtual environment if needed
echo "Setting up Python environment..."
python -m pip install --upgrade pip
python -m pip install gunicorn==21.2.0

# Set up directories
echo "Setting up directory structure..."
mkdir -p /var/data/db
mkdir -p /var/data/backups
mkdir -p /var/data/uploads
chmod -R 755 /var/data

# Find gunicorn executable
echo "Locating gunicorn..."
if command -v gunicorn &> /dev/null; then
    GUNICORN_PATH=$(command -v gunicorn)
    echo "Found gunicorn at: $GUNICORN_PATH"
else
    echo "Warning: gunicorn not found in PATH"
    GUNICORN_PATH="python -m gunicorn"
    echo "Will use: $GUNICORN_PATH"
fi

# Log versions for debugging
echo "Python version:"
python --version

# Log environment variables
echo "Environment variables:"
echo "FLASK_APP: $FLASK_APP"
echo "DATA_DIR: $DATA_DIR"

# Create a simple app.py that imports the real app for Render compatibility
echo "Creating app.py symlink or wrapper..."
if [ -f "wsgi.py" ] && [ ! -f "app.py" ]; then
    echo "Creating a simple app.py wrapper..."
    cat > app.py << EOL
# This is an auto-generated wrapper for compatibility with Render
from wsgi import app as application
app = application
EOL
fi

# Start the application
echo "Starting application with gunicorn..."
exec $GUNICORN_PATH app:app
