#!/usr/bin/env python
"""
Build script for the AMRS Maintenance Tracker Windows client application.
This script packages the application using PyInstaller and optionally
creates an installer using Inno Setup.
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

# Application information
APP_NAME = "AMRS Maintenance Tracker"
APP_VERSION = "1.0.0"
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description=f'Build {APP_NAME} {APP_VERSION}')
    
    parser.add_argument('--clean', action='store_true', help='Clean build directories before building')
    parser.add_argument('--debug', action='store_true', help='Build with debug information')
    parser.add_argument('--portable', action='store_true', help='Build portable version')
    parser.add_argument('--installer', action='store_true', help='Create installer using Inno Setup')
    parser.add_argument('--server-url', help='Pre-configure server URL')
    parser.add_argument('--skip-deps', action='store_true', help='Skip installing dependencies')
    parser.add_argument('--no-upx', action='store_true', help='Skip UPX compression')
    
    return parser.parse_args()

def check_dependencies():
    """Check and install required dependencies"""
    print("Checking and installing required dependencies...")
    
    requirements = [
        'PyQt6',
        'PyQt6-WebEngine',
        'requests',
        'keyring',
        'cryptography',
        'psycopg2-binary',
        'PyInstaller',
        'pywin32; platform_system=="Windows"',
        'pillow'
    ]
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade'] + requirements)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def clean_build_dirs():
    """Clean build and dist directories"""
    print("Cleaning build directories...")
    
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed {dir_name} directory")

def create_server_config(server_url):
    """Create a server configuration file"""
    print(f"Creating server configuration for {server_url}")
    
    config_dir = Path('dist') / 'config'
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = config_dir / 'server_config.json'
    with open(config_path, 'w') as f:
        f.write(f'{{"server_url": "{server_url}", "preconfigured": true}}')

def run_pyinstaller(args):
    """Run PyInstaller to package the application"""
    print("Running PyInstaller...")
    
    # Base PyInstaller command
    pyinstaller_args = [
        'pyinstaller',
        '--name', 'MaintenanceTracker',
        '--icon', 'resources/app_icon.ico',
        '--noconfirm',
    ]
    
    # Add windowed mode unless in debug mode
    if not args.debug:
        pyinstaller_args.append('--windowed')
    else:
        pyinstaller_args.append('--console')
    
    # Add UPX compression unless disabled
    if not args.no_upx:
        pyinstaller_args.extend(['--upx-dir', 'upx'])
    
    # Add hidden imports
    pyinstaller_args.extend([
        '--hidden-import=keyring.backends',
        '--hidden-import=keyring.backends.Windows',
        '--hidden-import=win32timezone',
    ])
    
    # Add data files
    pyinstaller_args.extend([
        '--add-data', 'resources;resources',
        '--add-data', '../static;static',
    ])
    
    # Main script
    if args.portable:
        pyinstaller_args.append('desktop_app_portable.py')
    else:
        pyinstaller_args.append('desktop_app.py')
    
    # Run PyInstaller
    subprocess.check_call(pyinstaller_args)

def create_installer(args):
    """Create Windows installer using Inno Setup"""
    print("Creating Windows installer...")
    
    # Path to Inno Setup compiler
    inno_setup_path = r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
    
    # If Inno Setup is not in the default location, try to find it
    if not os.path.exists(inno_setup_path):
        # Try Program Files location
        alt_path = r'C:\Program Files\Inno Setup 6\ISCC.exe'
        if os.path.exists(alt_path):
            inno_setup_path = alt_path
        else:
            # Try to find it in PATH
            try:
                inno_setup_path = 'iscc.exe'
                subprocess.check_call([inno_setup_path, '/?'], stdout=subprocess.DEVNULL)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Inno Setup Compiler (ISCC.exe) not found. Please install Inno Setup or add it to PATH.")
                return False
    
    # Run Inno Setup compiler
    setup_script = 'installer/setup.iss'
    if os.path.exists(setup_script):
        try:
            subprocess.check_call([inno_setup_path, setup_script])
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating installer: {e}")
            return False
    else:
        print(f"Setup script not found: {setup_script}")
        return False

def copy_portable_files(args):
    """Prepare the portable version with additional files"""
    print("Creating portable package...")
    
    # Create a portable directory
    portable_dir = Path('dist') / 'MaintenanceTrackerPortable'
    os.makedirs(portable_dir, exist_ok=True)
    
    # Copy the built executable and supporting files
    dist_files = Path('dist') / 'MaintenanceTracker'
    if not dist_files.exists():
        print("Built files not found. Make sure PyInstaller completed successfully.")
        return False
    
    # Copy all files from dist to portable directory
    shutil.copytree(dist_files, portable_dir, dirs_exist_ok=True)
    
    # Create data and logs directories
    os.makedirs(portable_dir / 'data', exist_ok=True)
    os.makedirs(portable_dir / 'logs', exist_ok=True)
    
    # Create README file with information about portable mode
    server_info = ""
    if args.server_url:
        server_info = f"\nThis version is pre-configured to connect to: {args.server_url}"
    
    with open(portable_dir / 'README.txt', 'w') as f:
        f.write(f"""
AMRS Maintenance Tracker {APP_VERSION} - Portable Edition{server_info}

ABOUT THIS APPLICATION
=====================
This is the portable version of AMRS Maintenance Tracker, which can run without installation.
The application is designed to work offline and sync data when connected to a server.

GETTING STARTED
==============
1. Simply double-click the MaintenanceTracker.exe file to run the application
2. On first run, enter your server URL, username and password
3. The application will work offline when no server connection is available

DATA STORAGE
==========
In portable mode, the application stores data in these locations:
- Database: data/offline_data.db
- Logs: logs/
- Configuration: config/

This allows you to run the application from external media like USB drives.

Built with Python {PYTHON_VERSION}
(c) AMRS Technologies
""")
    
    # Create a batch file to launch the application
    with open(portable_dir / 'Launch.bat', 'w') as f:
        f.write('@echo off\r\n')
        f.write('echo Launching AMRS Maintenance Tracker...\r\n')
        f.write('start "" "%~dp0MaintenanceTracker.exe"\r\n')
    
    print(f"Portable package created in {portable_dir}")
    return True

def create_zip_archive(portable_dir):
    """Create a ZIP archive of the portable version"""
    print("Creating ZIP archive...")
    
    import zipfile
    
    zip_path = f"{portable_dir}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(portable_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, os.path.dirname(portable_dir)))
    
    print(f"ZIP archive created: {zip_path}")
    return True

def main():
    """Main build function"""
    print(f"===== Building {APP_NAME} {APP_VERSION} =====")
    
    args = parse_arguments()
    
    # Clean build directories if requested
    if args.clean:
        clean_build_dirs()
    
    # Check and install dependencies unless skipped
    if not args.skip_deps:
        if not check_dependencies():
            print("Failed to install dependencies. Aborting build.")
            return 1
    
    # Create server configuration if specified
    if args.server_url:
        create_server_config(args.server_url)
    
    # Run PyInstaller
    try:
        run_pyinstaller(args)
    except subprocess.CalledProcessError as e:
        print(f"Error running PyInstaller: {e}")
        return 1
    
    # Create portable package if requested
    if args.portable:
        if not copy_portable_files(args):
            print("Failed to create portable package")
            return 1
        
        # Create ZIP archive of portable version
        create_zip_archive(Path('dist') / 'MaintenanceTrackerPortable')
    
    # Create installer if requested
    if args.installer:
        if not create_installer(args):
            print("Failed to create installer")
            return 1
    
    print(f"===== Build completed successfully =====")
    return 0

if __name__ == "__main__":
    sys.exit(main())
