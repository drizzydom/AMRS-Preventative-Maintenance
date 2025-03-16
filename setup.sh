#!/bin/bash

echo "=== Maintenance Tracker Setup Script ==="
echo "This script will set up a Python virtual environment with compatible dependencies."

# Check if Python 3.9+ is installed
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -lt 13 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        echo "Found compatible Python version: $PYTHON_VERSION"
        PYTHON_CMD="python3"
    else
        echo "Warning: Your Python version $PYTHON_VERSION may not be compatible."
        
        # Check if Python 3.9, 3.10, or 3.11 is available
        for ver in 3.9 3.10 3.11; do
            if command -v python$ver >/dev/null 2>&1; then
                echo "Found Python $ver, using it instead."
                PYTHON_CMD="python$ver"
                break
            fi
        done
        
        if [ -z "$PYTHON_CMD" ]; then
            echo "Error: Could not find a compatible Python version (3.9-3.11)."
            echo "Please install Python 3.9, 3.10, or 3.11 and try again."
            echo "On macOS, you can use: brew install python@3.11"
            exit 1
        fi
    fi
else
    echo "Error: Python 3 not found. Please install Python 3.9, 3.10, or 3.11."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Make reset_db.sh executable
if [ -f "reset_db.sh" ]; then
    chmod +x reset_db.sh
    echo "Made reset_db.sh executable"
fi

# Clean up any existing database
if [ -f "instance/maintenance.db" ]; then
    echo "Found existing database, creating backup..."
    mkdir -p backups
    cp instance/maintenance.db backups/maintenance_$(date +%Y%m%d_%H%M%S).db
    rm instance/maintenance.db
    echo "Old database removed"
fi

# Initialize database
echo "Initializing database..."
flask --app app init-db

echo "===== Setup Complete! ====="
echo "To start the application:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the application: python app.py"
echo "3. Open your browser to: http://localhost:5050"
echo "4. Login with: admin / admin"
echo ""
echo "To reset the database anytime, run: ./reset_db.sh"
