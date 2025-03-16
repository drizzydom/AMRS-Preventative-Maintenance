#!/bin/bash

echo "=== Maintenance Tracker Database Reset ==="
echo "This script will reset the database and initialize it with sample data."
echo "WARNING: All existing data will be lost."
echo ""
read -p "Continue? (y/n): " confirm

if [[ $confirm != [yY] ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
fi

# Delete the database file
rm -f instance/maintenance.db
echo "Database file deleted"

# Create the database and initialize it
flask --app app init-db
echo "Database initialized with sample data"

echo "===== Database Reset Complete! ====="
echo "You can now start the application with: python app.py"
