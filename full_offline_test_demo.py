#!/usr/bin/env python3
"""
Complete test and demonstration script for the offline mode functionality

This script will:
1. Create a test environment with the offline app running on a custom port
2. Show the synchronization between offline and online databases
3. Demonstrate a complete workflow from online to offline and back to online

Usage:
    python full_offline_test_demo.py [port]
"""
import os
import sys
import time
import subprocess
import threading
import webbrowser
import argparse
from datetime import datetime

# Set up argument parser
parser = argparse.ArgumentParser(description='Run a full offline mode test and demonstration')
parser.add_argument('port', nargs='?', default=None, 
                    help='Port to run the app on (default: 8080 or TEST_PORT env var)')
args = parser.parse_args()

# Determine the port to use
port = args.port or os.environ.get('TEST_PORT', '8080')

# Set environment variables
os.environ['PORT'] = port
os.environ['DISABLE_SQLCIPHER'] = 'true'
os.environ['OFFLINE_MODE'] = 'true'
os.environ['FLASK_ENV'] = 'development'
os.environ['TEST_MODE'] = 'true'
os.environ['DB_FILE'] = 'maintenance_full_test.db'  # Special DB just for this test

# Print start banner
print(f"=" * 80)
print(f"  AMRS Preventative Maintenance - Offline Mode Full Test Demo")
print(f"=" * 80)
print(f"Starting offline test sequence on port {port}")
print(f"Test database: {os.environ.get('DB_FILE')}")
print(f"")

# Step 1: Initialize the test environment
print("Step 1: Initializing test environment")
print("- Creating clean test database...")
if os.path.exists(os.path.join('instance', os.environ.get('DB_FILE', 'maintenance_full_test.db'))):
    try:
        os.remove(os.path.join('instance', os.environ.get('DB_FILE', 'maintenance_full_test.db')))
        print("- Removed existing test database")
    except Exception as e:
        print(f"- Warning: Could not remove existing database: {e}")

# Step 2: Import modules to run the app
print("Step 2: Preparing to run application")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    # Try to import the offline app
    from offline_app import app, initialize_database
    
    # Initialize the database
    print("- Initializing database with test data...")
    initialize_database()
    print("- Database initialized successfully")
    
    # Step 3: Start the web app in a separate thread
    print("Step 3: Starting web application")
    
    def run_app():
        """Run the Flask app in a separate thread"""
        print(f"- Starting offline app on port {port}...")
        app.run(host='0.0.0.0', port=int(port), debug=False, use_reloader=False)
    
    app_thread = threading.Thread(target=run_app)
    app_thread.daemon = True
    app_thread.start()
    
    # Wait for the app to start
    time.sleep(2)
    
    # Step 4: Open the browser
    print("Step 4: Opening web browser")
    print(f"- Access the application at: http://localhost:{port}")
    webbrowser.open(f"http://localhost:{port}")
    
    # Step 5: Provide test instructions
    print("\nTest instructions:")
    print("1. Log in with username 'admin' and password 'admin'")
    print("2. Observe the offline banner and status indicators")
    print("3. Create or modify some records")
    print("4. Test the sync button in the offline banner")
    print("5. Close the browser when finished testing")
    
    print("\nPress Ctrl+C to stop the test when finished...\n")
    
    # Keep the main thread running until user interrupts
    while True:
        time.sleep(1)
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Falling back to running as a subprocess")
    
    # Run as a subprocess instead
    offline_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_offline_app_test.py')
    subprocess.run([sys.executable, offline_app_path, port], env=os.environ)
    
except KeyboardInterrupt:
    print("\nTest interrupted by user. Shutting down...")
    
except Exception as e:
    print(f"\nError during test: {e}")
    
finally:
    print("\nTest completed. Thank you for testing the offline mode functionality.")
    print("See TESTING_OFFLINE_MODE.md for more detailed testing instructions.")
