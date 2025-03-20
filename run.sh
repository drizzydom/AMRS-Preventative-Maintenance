#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Update database schema
echo "Checking and updating database schema..."
python -m flask update-db-schema

# Run the Flask application
python app.py
