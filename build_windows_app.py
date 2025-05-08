#!/usr/bin/env python
"""
Build script for AMRS Maintenance Tracker Windows WebView2 Application
This script builds a standalone Windows executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Application information
APP_NAME = "AMRS Maintenance Tracker"
EXECUTABLE_NAME = "AMRSMaintenanceTracker"
VERSION = "1.0.0"
AUTHOR = "AMRS"

# Directory setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")
DIST_DIR = os.path.join(SCRIPT_DIR, "dist")
SPEC_FILE = os.path.join(SCRIPT_DIR, f"{EXECUTABLE_NAME}.spec")

# Files to include
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "webview_app.py")
BOOTSTRAP_SCRIPT = os.path.join(SCRIPT_DIR, "app_bootstrap.py")
ICON_FILE = os.path.join(SCRIPT_DIR, "static", "img", "favicon.ico")

# Content folders that need to be copied
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "templates")
STATIC_DIR = os.path.join(SCRIPT_DIR, "static")
APP_DIR = os.path.join(SCRIPT_DIR, "app")

def ensure_directories():
    """Ensure build directories exist"""
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)

def clean_directories():
    """Clean build and dist directories"""
    print("Cleaning build directories...")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    if os.path.exists(DIST_DIR):
        shutil.rmtree(BUILD_DIR)
    if os.path.exists(SPEC_FILE):
        os.remove(SPEC_FILE)
    ensure_directories()

def create_version_file():
    """Create a version file for the application"""
    version_file = os.path.join(BUILD_DIR, "version.txt")
    print(f"Creating version file: {version_file}")
    
    with open(version_file, "w") as f:
        f.write(f"AppName={APP_NAME}\n")
        f.write(f"Version={VERSION}\n")
        f.write(f"Author={AUTHOR}\n")
        f.write(f"BuildDate={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return version_file

def run_pyinstaller(debug=False, onefile=True):
    """Run PyInstaller to build the executable"""
    print(f"Building {'debug' if debug else 'release'} version of {APP_NAME}...")
    
    # Base PyInstaller command
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        f"--name={EXECUTABLE_NAME}",
    ]
    
    # Add debug flags if requested
    if debug:
        cmd.append("--debug=all")
    
    # Set packaging mode (onefile or onedir)
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    # Add icon if it exists
    if os.path.exists(ICON_FILE):
        cmd.append(f"--icon={ICON_FILE}")
    else:
        print(f"Warning: Icon file not found at {ICON_FILE}")
    
    # Add Windows subsystem (no console)
    cmd.append("--windowed")
    
    # Add data files
    # Templates
    if os.path.exists(TEMPLATE_DIR):
        cmd.append(f"--add-data={TEMPLATE_DIR};templates")
    else:
        print(f"Warning: Templates directory not found at {TEMPLATE_DIR}")
    
    # Static files
    if os.path.exists(STATIC_DIR):
        cmd.append(f"--add-data={STATIC_DIR};static")
    else:
        print(f"Warning: Static directory not found at {STATIC_DIR}")
    
    # App directory
    if os.path.exists(APP_DIR):
        cmd.append(f"--add-data={APP_DIR};app")
    else:
        print(f"Warning: App directory not found at {APP_DIR}")
    
    # Add bootstrap script
    if os.path.exists(BOOTSTRAP_SCRIPT):
        cmd.append(f"--add-data={BOOTSTRAP_SCRIPT};.")
    else:
        print(f"Warning: Bootstrap script not found at {BOOTSTRAP_SCRIPT}")
    
    # Add main script
    cmd.append(MAIN_SCRIPT)
    
    # Print the command
    print(f"Running PyInstaller: {' '.join(cmd)}")
    
    # Run PyInstaller
    process = subprocess.run(cmd, check=True)
    
    if process.returncode != 0:
        print(f"Error: PyInstaller failed with return code {process.returncode}")
        return False
    
    print(f"PyInstaller completed successfully.")
    return True

def build_app(clean=True, debug=False, onefile=True):
    """Build the Windows application"""
    # Initialize directories
    if clean:
        clean_directories()
    else:
        ensure_directories()
    
    # Run PyInstaller
    success = run_pyinstaller(debug=debug, onefile=onefile)
    
    if success:
        # Get the path to the output executable
        if onefile:
            exe_path = os.path.join(DIST_DIR, f"{EXECUTABLE_NAME}.exe")
        else:
            exe_path = os.path.join(DIST_DIR, EXECUTABLE_NAME, f"{EXECUTABLE_NAME}.exe")
        
        if os.path.exists(exe_path):
            print(f"Build successful! Executable created at: {exe_path}")
            print(f"You can now run the application by double-clicking the executable.")
        else:
            print(f"Error: Expected executable not found at {exe_path}")
            return False
    else:
        print("Build failed.")
        return False
    
    return True

def main():
    """Main entry point for the build script"""
    parser = argparse.ArgumentParser(description=f"Build {APP_NAME} Windows Application")
    parser.add_argument("--no-clean", action="store_true", help="Don't clean build directories before building")
    parser.add_argument("--debug", action="store_true", help="Build a debug version with console")
    parser.add_argument("--onedir", action="store_true", help="Build as a directory instead of a single file")
    args = parser.parse_args()
    
    print(f"Starting build process for {APP_NAME} v{VERSION}")
    success = build_app(
        clean=not args.no_clean,
        debug=args.debug,
        onefile=not args.onedir
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    import datetime
    sys.exit(main())