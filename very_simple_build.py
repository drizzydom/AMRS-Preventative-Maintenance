"""
Very Simple Build Script for AMRS Maintenance Tracker
Uses direct PyInstaller commands to avoid deep dependency analysis issues
"""
import os
import sys
import shutil
import subprocess

def clean_output():
    """Clean previous build artifacts"""
    print("Cleaning previous build artifacts...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Remove spec files
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            print(f"Removing {file}...")
            os.unlink(file)

def run_build():
    """Run PyInstaller with direct command line options to avoid analysis issues"""
    print("Building application...")
    
    # Build the base command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--name=AMRSMaintenanceTracker",
        "--onefile",  # Use onefile for simplicity
        "--windowed",  # No console window in final app
        "--log-level=INFO"
    ]
    
    # Add data files
    cmd.extend([
        "--add-data=templates;templates",
        "--add-data=static;static"
    ])
    
    # Add important imports directly to avoid deep analysis
    cmd.extend([
        "--hidden-import=sqlite3",
        "--hidden-import=flask",
        "--hidden-import=flask_login",
        "--hidden-import=flask_sqlalchemy",
        "--hidden-import=werkzeug",
        "--hidden-import=jinja2",
        "--hidden-import=sqlalchemy",
        "--hidden-import=cefpython3",
    ])
    
    # Exclude problematic modules
    cmd.extend([
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=numpy",
        "--exclude-module=scipy",
        "--exclude-module=pandas",
        "--exclude-module=PIL"
    ])
    
    # Add the main script
    cmd.append("desktop_app_browser.py")  # Using the browser version which avoids CEF
    
    # Run the command
    print(f"Running command: {' '.join(cmd)}")
    return subprocess.call(cmd)

def main():
    print("=" * 80)
    print("Very Simple Build Script for AMRS Maintenance Tracker")
    print("=" * 80)
    
    # Clean previous builds
    clean_output()
    
    # Run the build
    result = run_build()
    
    if result == 0:
        print("=" * 80)
        print("Build completed successfully!")
        print("=" * 80)
        print(f"Output: {os.path.abspath('dist/AMRSMaintenanceTracker.exe')}")
    else:
        print("=" * 80)
        print(f"Build failed with error code: {result}")
        print("=" * 80)
    
    return result

if __name__ == "__main__":
    sys.exit(main())
