#!/bin/bash
# Simple script to run the application in development mode

# Set Flask environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_RUN_PORT=5050  # Use port 5050 instead of default 5000

# Initialize the database (creates tables and admin user if needed)
echo "Checking database initialization..."
python initialize_db.py

# Run the Flask development server
echo "Starting Flask development server..."
python app.py
