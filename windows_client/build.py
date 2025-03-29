#!/usr/bin/env python3
"""
Build script for creating a portable Windows executable
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import zipfile
import argparse
import datetime

APP_NAME = "Maintenance Tracker"
APP_VERSION = "1.0.0"

def run_command(command):
    """Run a shell command and print output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=True)
    return result

def create_executable():
    """Create standalone executable with PyInstaller"""
    print(f"Building {APP_NAME} v{APP_VERSION}...")
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        run_command("pip install pyinstaller")
    
    # Clean previous build
    dist_dir = Path("dist")
    build_dir = Path("build")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Create executable
    cmd = [
        "pyinstaller",
        "--name", f"{APP_NAME.replace(' ', '')}",
        "--onefile",  # Create a single executable
        "--windowed", # Don't show console window
        "--clean",    # Clean PyInstaller cache before building
        "--add-data", "LICENSE;.", # Add license file
    ]
    
    # Check for icon file and add it if it exists
    icon_path = Path("app_icon.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # Add main.py
    cmd.append("main.py")
    
    run_command(" ".join(cmd))
    
    print("Executable build completed successfully!")
    return Path("dist") / f"{APP_NAME.replace(' ', '')}.exe"

def create_portable_package():
    """Create a portable package with all necessary files"""
    print("Creating portable package...")
    
    # Create base portable directory
    portable_dir = Path("dist") / f"{APP_NAME.replace(' ', '')}_Portable"
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    portable_dir.mkdir(exist_ok=True)
    
    # Copy executable
    exe_path = Path("dist") / f"{APP_NAME.replace(' ', '')}.exe"
    if not exe_path.exists():
        print("Error: Executable not found. Build it first.")
        return False
    
    shutil.copy(exe_path, portable_dir / exe_path.name)
    
    # Create a portable marker file
    with open(portable_dir / "portable.txt", "w") as f:
        f.write(f"{APP_NAME} Portable Edition\nVersion: {APP_VERSION}\nCreated: {datetime.datetime.now()}")
    
    # Create README file
    with open(portable_dir / "README.txt", "w") as f:
        f.write(f"""
{APP_NAME} {APP_VERSION} - Portable Edition

ABOUT THIS APPLICATION
=====================
This is the portable version of {APP_NAME}, which can be run without installation.
The application is designed to work offline and sync data when connected to the server.

GETTING STARTED
==============
1. Simply double-click the {APP_NAME.replace(' ', '')}.exe file to run the application
2. On first run, enter your server URL, username and password
3. Check "Remember my credentials" to enable automatic login

DATA STORAGE
===========
Even in portable mode, the application stores its data in these locations:
- User settings: %APPDATA%\\{APP_NAME}
- Logs: %USERPROFILE%\\.amrs\\logs
- Offline database: %USERPROFILE%\\.amrs\\offline_cache.db

SUPPORT
=======
For support or to report issues, please contact your system administrator.
""")
    
    # Create ZIP file with timestamp (optional)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = Path("dist") / f"{APP_NAME.replace(' ', '')}_Portable_{APP_VERSION}_{timestamp}.zip"
    
    print(f"Creating ZIP archive at: {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in portable_dir.glob("**/*"):
            zipf.write(file, file.relative_to(portable_dir))
    
    print(f"Portable package created successfully at: {portable_dir}")
    print(f"Portable ZIP created at: {zip_path}")
    return True

def main():
    """Main build process"""
    parser = argparse.ArgumentParser(description=f"Build {APP_NAME} as a portable application")
    parser.add_argument('--exe-only', action='store_true', help="Only create the executable without portable package")
    args = parser.parse_args()
    
    # Build the executable
    create_executable()
    
    if not args.exe_only:
        # Create the portable package
        create_portable_package()
        
    print("Build process completed!")

if __name__ == "__main__":
    main()
