#!/usr/bin/env python3
"""
Wrapper script to run the offline app with SQLCipher disabled

This script will set the DISABLE_SQLCIPHER environment variable
and then run the offline app.
"""
import os
import sys
import subprocess

# Set environment variable to disable SQLCipher
os.environ['DISABLE_SQLCIPHER'] = 'true'

# Optional: Remove existing database file if it's corrupted
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'maintenance.db')
if os.environ.get('RECREATE_DB', '').lower() == 'true' and os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"Removed database file {db_path}")
    except Exception as e:
        print(f"Error removing database file: {e}")

# Run the offline app
print("Starting offline app with SQLCipher disabled...")
offline_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'offline_app.py')

# Get port from environment or use default
port = os.environ.get('PORT', '5000')

# Run the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    # Try to import and run directly first
    from offline_app import app
    print(f"Running app on port {port}...")
    app.run(host='0.0.0.0', port=int(port), debug=True)
except ImportError as e:
    # Fall back to subprocess if import fails
    print(f"Import failed: {e}, falling back to subprocess")
    subprocess.run([sys.executable, offline_app_path], env=os.environ)
