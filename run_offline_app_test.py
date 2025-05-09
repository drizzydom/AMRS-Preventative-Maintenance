#!/usr/bin/env python3
"""
Test script to run the offline app on a different port for browser testing

This script allows running the AMRS Preventative Maintenance offline app
on a separate port for testing while the main application is running.

Usage:
    python run_offline_app_test.py [port]

    You can also set the port using the TEST_PORT environment variable:
    TEST_PORT=8080 python run_offline_app_test.py

Examples:
    python run_offline_app_test.py 8080  # Run on port 8080
    TEST_PORT=9090 python run_offline_app_test.py  # Run on port 9090
"""
import os
import sys
import subprocess
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description='Run the offline app on a test port')
parser.add_argument('port', nargs='?', default=None, 
                    help='Port to run the app on (default: 8080 or TEST_PORT env var)')
parser.add_argument('--initialize-only', action='store_true',
                    help='Only initialize the database, do not start the app')
args = parser.parse_args()

# Determine the port to use (priority: command line arg > env var > default)
port = args.port or os.environ.get('TEST_PORT', '8080')

# Set environment variables
os.environ['PORT'] = port
os.environ['DISABLE_SQLCIPHER'] = 'true'
os.environ['OFFLINE_MODE'] = 'true'
os.environ['FLASK_ENV'] = 'development'
os.environ['TEST_MODE'] = 'true'

# Optional: Use a different database file for testing
os.environ['DB_FILE'] = 'maintenance_test.db'

# Print startup information
print(f"==== AMRS Preventative Maintenance Offline Test ====")
print(f"Starting offline app for testing on port {port}")
print(f"Access the application at: http://localhost:{port}")
print(f"Database file: {os.environ.get('DB_FILE', 'maintenance.db')}")
print(f"=================================================")

# Run the offline app
offline_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'offline_app.py')

# Run the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    # Try to import and run directly first
    from offline_app import app, initialize_database
    
    # Initialize the database
    initialize_database()
    print("Database initialized successfully.")
    
    # If initialize-only flag is set, exit after initialization
    if args.initialize_only:
        print("Database initialization complete. Exiting without starting app.")
        sys.exit(0)
    
    print(f"Running app on port {port}...")
    app.run(host='0.0.0.0', port=int(port), debug=True)
except ImportError as e:
    # Fall back to subprocess if import fails
    print(f"Import failed: {e}, falling back to subprocess")
    subprocess.run([sys.executable, offline_app_path], env=os.environ)
except Exception as e:
    print(f"Error starting the app: {e}")
    sys.exit(1)
