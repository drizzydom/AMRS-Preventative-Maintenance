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
import json
import platform

APP_NAME = "Maintenance Tracker"
APP_VERSION = "1.0.0"

def run_command(command, verbose=True):
    """Run a shell command and print output"""
    print(f"Running: {command}")
    
    # For PyInstaller, we want to see all output for diagnostics
    if verbose:
        # Use Popen to capture output in real-time
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
            
        # Wait for process to complete
        process.wait()
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
        
        return process
    else:
        # For other commands, just run and check result
        result = subprocess.run(command, shell=True, check=True)
        return result

def create_server_config(server_url):
    """Create a server configuration file that will be included in the build"""
    if server_url:
        print(f"Creating build with pre-configured server URL: {server_url}")
        config = {
            "server_url": server_url,
            "preconfigured": True
        }
        
        # Write to a temporary file that will be included in the build
        with open("server_config.json", "w") as f:
            json.dump(config, f)
        
        return True
    return False

def create_executable(server_url=None):
    """Create standalone executable with PyInstaller"""
    print(f"Building {APP_NAME} v{APP_VERSION}...")
    
    # Create server config if URL provided
    has_server_config = create_server_config(server_url)
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
        print(f"Using PyInstaller version: {PyInstaller.__version__}")
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
    
    # Use the correct path separator for the platform
    if platform.system() == "Windows":
        path_sep = ";"
    else:
        path_sep = ":"
    
    # Create executable
    cmd = [
        "pyinstaller",
        "--name", f"{APP_NAME.replace(' ', '')}",
        "--onefile",  # Create a single executable
        "--windowed", # Don't show console window
        "--clean",    # Clean PyInstaller cache before building
        "--log-level=DEBUG",  # More verbose logging
    ]
    
    # Add data files with platform-specific separator
    license_path = os.path.abspath("LICENSE")
    if os.path.exists(license_path):
        cmd.extend(["--add-data", f"{license_path}{path_sep}."]) 
    else:
        print("Warning: LICENSE file not found. Continuing without it.")
    
    # Add server config if created
    if has_server_config:
        config_path = os.path.abspath("server_config.json")
        cmd.extend(["--add-data", f"{config_path}{path_sep}."])
    
    # Check for icon file and add it if it exists
    icon_path = Path("app_icon.ico")
    if icon_path.exists():
        icon_abs_path = os.path.abspath(icon_path)
        cmd.extend(["--icon", icon_abs_path])
    
    # Add main.py with absolute path
    main_path = os.path.abspath("main.py")
    cmd.append(main_path)
    
    # Run PyInstaller with command arguments
    try:
        print("Starting PyInstaller build with arguments:")
        for arg in cmd:
            print(f"  {arg}")
        
        # On Windows, it's better to use subprocess with a list of arguments
        # rather than a joined string
        if platform.system() == "Windows":
            run_command(cmd, verbose=True)
        else:
            run_command(" ".join(cmd), verbose=True)
            
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller build failed with exit code {e.returncode}")
        print("Please check the output above for specific error messages.")
        sys.exit(1)
    
    # Clean up temporary config file
    if has_server_config and os.path.exists("server_config.json"):
        os.remove("server_config.json")
    
    print("Executable build completed successfully!")
    return Path("dist") / f"{APP_NAME.replace(' ', '')}.exe"

def create_portable_package(server_url=None):
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
    
    # Server info in README
    server_info = ""
    if server_url:
        server_info = f"\nThis version is pre-configured to connect to: {server_url}"
    
    # Create README file
    with open(portable_dir / "README.txt", "w") as f:
        f.write(f"""
{APP_NAME} {APP_VERSION} - Portable Edition{server_info}

ABOUT THIS APPLICATION
=====================
This is the portable version of {APP_NAME}, which can be run without installation.
The application is designed to work offline and sync data when connected to the server.

GETTING STARTED
==============
1. Simply double-click the {APP_NAME.replace(' ', '')}.exe file to run the application
2. On first run, enter your username and password{'' if server_url else ' and server URL'}
3. Check "Remember my credentials" to enable automatic login

DATA STORAGE
===========
Even in portable mode, the application stores its data in these locations:
- User settings: %APPDATA%\\{APP_NAME} or in the data folder next to the executable
- Logs: In the logs folder next to the executable

SUPPORT
=======
For support or to report issues, please contact your system administrator.
""")
    
    # Create ZIP file with timestamp and server info
    zip_name = f"{APP_NAME.replace(' ', '')}_Portable_{APP_VERSION}"
    
    if server_url:
        # Add server domain to filename (safely)
        try:
            from urllib.parse import urlparse
            domain = urlparse(server_url).netloc
            if domain:
                # Remove port numbers and special chars for filename safety
                domain = domain.split(':')[0].replace('.', '-')
                zip_name += f"_{domain}"
        except:
            pass
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    zip_name += f"_{timestamp}.zip"
    zip_path = Path("dist") / zip_name
    
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
    parser.add_argument('--server-url', help="Pre-configure the application with a specific server URL")
    args = parser.parse_args()
    
    # Build the executable with server URL if provided
    create_executable(args.server_url)
    
    if not args.exe_only:
        # Create the portable package
        create_portable_package(args.server_url)
        
    print("Build process completed!")
    
    if args.server_url:
        print(f"Application was pre-configured to use server: {args.server_url}")

if __name__ == "__main__":
    main()
