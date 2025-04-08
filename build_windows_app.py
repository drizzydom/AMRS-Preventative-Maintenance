"""
Simplified Windows application builder that creates a launcher for
AMRS Preventative Maintenance system.

This script:
1. Creates a simple Python application that launches the web interface
2. Uses PyInstaller if available, but falls back to a simple script if not
3. Works without requiring Microsoft Visual C++ Build Tools
"""

import os
import sys
import subprocess
import time
import urllib.request
from pathlib import Path

# Configuration
APP_NAME = "AMRS Maintenance Tracker"
APP_VERSION = "1.0.0"
SERVER_URL = "https://amrs-preventative-maintenance.onrender.com"
OUTPUT_DIR = "dist"
SCRIPT_NAME = "amrs_launcher.py"

print(f"Building {APP_NAME} v{APP_VERSION}")
print(f"This launcher will connect to: {SERVER_URL}")
print("-----------------------------------------------")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Create a simple launcher script
with open(SCRIPT_NAME, 'w') as f:
    f.write(f"""
# Simple launcher script for {APP_NAME}
import webbrowser
import os
import sys
import time

print("Starting {APP_NAME} v{APP_VERSION}")
print("Connecting to {SERVER_URL}")

try:
    # Try to ping the server first
    import urllib.request
    import urllib.error
    
    print("Checking server connection...")
    try:
        with urllib.request.urlopen("{SERVER_URL}/health") as response:
            if response.status == 200:
                print("Server is online!")
            else:
                print(f"Server returned status code: {{response.status}}")
    except urllib.error.URLError:
        print("Warning: Could not connect to server. It may be offline.")
    
    # Open the web browser regardless
    print("Opening application in your web browser...")
    webbrowser.open("{SERVER_URL}")
    print("Application launched successfully!")
except Exception as e:
    print(f"Error: {{str(e)}}")
    print("Please try again or contact support.")

# Keep console window open if run directly
if getattr(sys, 'frozen', False):
    print("\\nPress Enter to close this window...")
    input()
""")

print(f"Created launcher script: {SCRIPT_NAME}")

# Try to use PyInstaller if installed
try:
    import PyInstaller
    print("PyInstaller found! Attempting to build executable...")
    
    # Basic PyInstaller command without complex dependencies
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--name', APP_NAME.replace(' ', ''),
        '--onefile',
        '--console',  # Use console mode for simplicity
        SCRIPT_NAME
    ]
    
    # Try to build with PyInstaller
    subprocess.run(cmd, check=True)
    exe_path = os.path.join('dist', f"{APP_NAME.replace(' ', '')}.exe")
    
    if os.path.exists(exe_path):
        print(f"\n✅ SUCCESS! Executable created: {os.path.abspath(exe_path)}")
    else:
        print("\n⚠️ PyInstaller didn't create the expected executable.")
        raise Exception("Executable not found")
        
except Exception as e:
    print(f"\n⚠️ Could not build executable with PyInstaller: {str(e)}")
    print("Creating a simple batch file launcher instead...")
    
    # Create a batch file as an alternative
    batch_path = os.path.join(OUTPUT_DIR, f"{APP_NAME.replace(' ', '')}.bat")
    with open(batch_path, 'w') as f:
        f.write(f"""@echo off
echo Starting {APP_NAME} v{APP_VERSION}
echo Connecting to {SERVER_URL}
echo.
python "%~dp0\\{SCRIPT_NAME}" || (
    echo.
    echo Python not found! Please install Python from python.org
    pause
)
""")
    
    # Copy the Python script to the dist folder
    import shutil
    shutil.copy(SCRIPT_NAME, os.path.join(OUTPUT_DIR, SCRIPT_NAME))
    
    print(f"\n✅ ALTERNATIVE SOLUTION: Created batch file launcher: {os.path.abspath(batch_path)}")
    print(f"To use it:")
    print(f"  1. Make sure Python is installed on your system")
    print(f"  2. Double-click the batch file to launch the application")

print("\nDone! The application will connect to:")
print(f"  {SERVER_URL}")

# Clean up
print("\nCleaning up temporary files...")
try:
    # Keep the Python script, but remove any PyInstaller spec files
    if os.path.exists(f"{APP_NAME.replace(' ', '')}.spec"):
        os.remove(f"{APP_NAME.replace(' ', '')}.spec")
    
    # Clean up PyInstaller build folder if it exists
    build_dir = "build"
    if os.path.exists(build_dir) and os.path.isdir(build_dir):
        print(f"Removing {build_dir} directory...")
        shutil.rmtree(build_dir, ignore_errors=True)
except Exception as e:
    print(f"Warning during cleanup: {str(e)}")

print("\nYou can distribute the files from the 'dist' folder to users.")
