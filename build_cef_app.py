"""
Build script for AMRS Maintenance Tracker with CEF Python
Uses custom hooks to avoid dependency analysis issues
"""
import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

def clean_build_directories():
    """Clean previous build artifacts"""
    print("Cleaning build directories...")
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
    
    print("Done cleaning.")

def apply_cef_python_patch():
    """Apply the patch to make CEF Python work with Python 3.10"""
    print("\nApplying CEF Python compatibility patch...")
    
    # Check current Python version
    import sys
    python_version = sys.version_info
    
    if python_version.major == 3 and python_version.minor < 10:
        print(f"✓ Python {python_version.major}.{python_version.minor} detected - CEF Python should be compatible.")
        return True
    
    print(f"Python {python_version.major}.{python_version.minor} detected - CEF Python 66.1 is not officially compatible.")
    print("\nOptions to resolve this issue:")
    print("  1. Use an alternative browser-based approach")
    print("  2. Create a Python 3.9 virtual environment")
    print("  3. Try a direct build without patching (may fail)")
    print("  4. Try experimental patching (unstable)")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == '1':
        return use_browser_alternative()
    elif choice == '2':
        return setup_python39_env()
    elif choice == '3':
        print("Proceeding with build without patching...")
        return True
    elif choice == '4':
        return try_experimental_patch()
    else:
        print("Invalid choice. Defaulting to option 1 (browser alternative).")
        return use_browser_alternative()

def use_browser_alternative():
    """Use a browser-based alternative instead of CEF"""
    print("\nSetting up browser-based alternative...")
    
    # Create the alternative desktop app file
    browser_app_file = os.path.join(os.path.dirname(__file__), "desktop_app_browser.py")
    
    # Ask if user wants to use this file
    if os.path.exists(browser_app_file):
        print("A browser-based app file already exists.")
        use_existing = input("Do you want to use the existing file? (y/n): ")
        if use_existing.lower() == 'y':
            return setup_browser_build()
    
    print("Creating browser-based app file...")
    with open(browser_app_file, "w") as f:
        f.write("""
\"\"\"
AMRS Maintenance Tracker - Browser Version
Uses the system's web browser instead of CEF
\"\"\"
import os
import sys
import time
import logging
import subprocess
import webbrowser
import socket
import signal
import platform

# Set up paths
APP_NAME = "AMRS Maintenance Tracker"
APP_VERSION = "1.0.0"
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".amrs-maintenance")
LOG_PATH = os.path.join(APP_DATA_DIR, "desktop_app.log")

# Create app data directory if it doesn't exist
os.makedirs(APP_DATA_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def find_available_port():
    \"\"\"Find an available port to use\"\"\"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def start_flask_server(port):
    \"\"\"Start the Flask server process\"\"\"
    app_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    
    if not os.path.exists(app_script):
        logger.error(f"Flask app not found at {app_script}")
        return None
        
    logger.info(f"Starting Flask server on port {port}")
    
    cmd = [
        sys.executable, 
        app_script,
        "--port", str(port)
    ]
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if process.poll() is not None:
            logger.error(f"Flask process failed to start")
            return None
        
        return process
    except Exception as e:
        logger.error(f"Error starting Flask: {e}")
        return None

def wait_for_flask_server(port, timeout=30):
    \"\"\"Wait for the Flask server to become available\"\"\"
    logger.info(f"Waiting for Flask server on port {port}")
    start_time = time.time()
    
    while (time.time() - start_time) < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            if sock.connect_ex(('localhost', port)) == 0:
                sock.close()
                logger.info(f"Flask server is ready on port {port}")
                return True
            sock.close()
        except:
            pass
        time.sleep(0.5)
    
    logger.error(f"Timed out waiting for Flask server on port {port}")
    return False

def main():
    \"\"\"Main function\"\"\"
    print(f"Starting {APP_NAME} v{APP_VERSION}")
    
    # Start Flask server
    port = find_available_port()
    flask_process = start_flask_server(port)
    
    if not flask_process:
        print("Failed to start Flask server.")
        input("Press Enter to exit...")
        return 1
    
    # Wait for Flask to start
    url = f"http://localhost:{port}"
    if not wait_for_flask_server(port):
        print("Timed out waiting for Flask to start.")
        if flask_process:
            flask_process.terminate()
        input("Press Enter to exit...")
        return 1
    
    # Open browser
    print(f"Opening {url} in default browser...")
    webbrowser.open(url)
    
    print(f"\n{APP_NAME} is running!")
    print(f"URL: {url}")
    print("Close this window to shut down the application.")
    
    # Keep running until terminated
    try:
        while True:
            time.sleep(1)
            # Check if Flask process is still running
            if flask_process.poll() is not None:
                print("Flask server stopped unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Terminate Flask when we exit
        if flask_process:
            if platform.system() == "Windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(flask_process.pid)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                flask_process.terminate()
    
    print("Application shut down.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
""")
    
    print(f"✓ Created {browser_app_file}")
    return setup_browser_build()

def setup_browser_build():
    """Set up the spec file for browser-based build"""
    global MAIN_SCRIPT
    MAIN_SCRIPT = "desktop_app_browser.py"
    print(f"Using {MAIN_SCRIPT} for build")
    return True

def setup_python39_env():
    """Guide the user to set up a Python 3.9 environment"""
    print("\nSetting up Python 3.9 Environment:\n")
    print("1. Download and install Python 3.9 from: https://www.python.org/downloads/release/python-3913/")
    print("   - For Windows, download 'Windows installer (64-bit)'")
    print("   - Make sure to check 'Add Python to PATH' during installation")
    print("\n2. Create a new virtual environment with Python 3.9:")
    print("   - Windows (after installation):")
    print("     py -3.9 -m venv venv_py39")
    print("     or")
    print("     \"C:\\Program Files\\Python39\\python.exe\" -m venv venv_py39")
    print("\n3. Activate the new environment:")
    print("   - Windows: venv_py39\\Scripts\\activate")
    print("   - Linux/Mac: source venv_py39/bin/activate")
    print("\n4. Install required packages:")
    print("   pip install cefpython3==66.1 flask==2.2.5 flask_sqlalchemy==3.0.5 flask_login==0.6.2 pyinstaller==6.0.0")
    print("\n5. Run this build script from the Python 3.9 environment")
    
    print("\nAlternatively, you can use our PowerShell helper script:")
    powershell_script = os.path.join(os.path.dirname(__file__), "setup_py39.ps1")
    
    with open(powershell_script, "w") as f:
        f.write("""
# PowerShell script to help set up Python 3.9 environment
Write-Host "Setting up Python 3.9 environment for AMRS Maintenance Tracker" -ForegroundColor Cyan

# Check if Python 3.9 is installed
$py39Path = "C:\\Program Files\\Python39\\python.exe"
$py39Installed = Test-Path $py39Path

if (-not $py39Installed) {
    Write-Host "Python 3.9 not found. Please download and install it from:" -ForegroundColor Yellow
    Write-Host "https://www.python.org/downloads/release/python-3913/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Write-Host "After installation, run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# Create virtual environment
Write-Host "Creating Python 3.9 virtual environment..." -ForegroundColor Cyan
& $py39Path -m venv venv_py39

# Activate virtual environment and install packages
Write-Host "Installing required packages..." -ForegroundColor Cyan
& .\\venv_py39\\Scripts\\Activate.ps1
pip install cefpython3==66.1 flask==2.2.5 flask_sqlalchemy==3.0.5 flask_login==0.6.2 pyinstaller==6.0.0

Write-Host "`nEnvironment setup complete!" -ForegroundColor Green
Write-Host "`nTo activate this environment in the future, run:" -ForegroundColor Cyan
Write-Host ".\\venv_py39\\Scripts\\Activate.ps1" -ForegroundColor White
Write-Host "`nTo build the application, run:" -ForegroundColor Cyan
Write-Host "python build_cef_app.py" -ForegroundColor White

Read-Host "`nPress Enter to exit"
""")
    
    print(f"\nCreated PowerShell helper script: {powershell_script}")
    print("Run it with: powershell -ExecutionPolicy Bypass -File setup_py39.ps1\n")
    
    # Also create a batch file version for those who can't run PowerShell scripts
    batch_script = os.path.join(os.path.dirname(__file__), "setup_py39.bat")
    
    with open(batch_script, "w") as f:
        f.write("""@echo off
echo Setting up Python 3.9 environment for AMRS Maintenance Tracker
echo.

REM Check if Python 3.9 is installed
if exist "C:\\Program Files\\Python39\\python.exe" (
    echo Found Python 3.9
) else (
    echo Python 3.9 not found. Please download and install it from:
    echo https://www.python.org/downloads/release/python-3913/
    echo Make sure to check 'Add Python to PATH' during installation
    echo After installation, run this script again.
    pause
    exit /b
)

echo Creating Python 3.9 virtual environment...
"C:\\Program Files\\Python39\\python.exe" -m venv venv_py39

echo Installing required packages...
call venv_py39\\Scripts\\activate.bat
pip install cefpython3==66.1 flask==2.2.5 flask_sqlalchemy==3.0.5 flask_login==0.6.2 pyinstaller==6.0.0

echo.
echo Environment setup complete!
echo.
echo To activate this environment in the future, run:
echo venv_py39\\Scripts\\activate.bat
echo.
echo To build the application, run:
echo python build_cef_app.py
echo.

pause
""")
    
    print(f"Created batch helper script: {batch_script}")
    print("Run it by double-clicking setup_py39.bat\n")
    
    choice = input("\nDo you want to continue with the current environment? (y/n): ")
    if choice.lower() == 'y':
        return True
    else:
        return False

def try_experimental_patch():
    """Try an experimental direct patch of the CEF Python module"""
    import importlib.util
    
    # Find the cefpython module
    try:
        spec = importlib.util.find_spec("cefpython3")
        if not spec or not spec.origin:
            print("Could not find cefpython3 module")
            return False
        
        init_file = spec.origin
        print(f"Found cefpython3 __init__.py at: {init_file}")
        
        # Create backup if needed
        backup_file = init_file + ".bak"
        if not os.path.exists(backup_file):
            import shutil
            shutil.copy2(init_file, backup_file)
            print(f"Created backup at {backup_file}")
        
        # Read file content
        with open(init_file, 'r') as f:
            lines = f.readlines()
        
        # Find and modify the version check
        for i in range(len(lines)):
            if "raise Exception" in lines[i] and "Python version not supported" in lines[i]:
                # Insert a try-except block to bypass the exception
                lines[i] = "        try: pass  # Skip Python version check\n"
                
        # Write modified file
        with open(init_file, 'w') as f:
            f.writelines(lines)
            
        print("✓ Applied experimental patch")
        print("Note: This might still fail during import")
        
        # Test import
        try:
            import cefpython3
            print("✓ Successfully imported cefpython3!")
            return True
        except Exception as e:
            print(f"× Failed to import cefpython3: {e}")
            
            # Try to restore from backup
            try:
                shutil.copy2(backup_file, init_file)
                print("Restored from backup")
            except:
                print("Warning: Failed to restore from backup")
                
            return False
            
    except Exception as e:
        print(f"Error applying patch: {e}")
        return False

def create_spec_file():
    """Create a custom PyInstaller spec file"""
    print("Creating custom spec file...")
    
    # Get the current script directory
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Create a simple PyInstaller command
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# Explicitly copy app.py to the root of the distribution
added_files = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('app.py', '.'),
]

# Include models.py if it exists
if os.path.exists('models.py'):
    added_files.append(('models.py', '.'))

# Copy any database files if they exist
for db_file in Path('.').glob('*.db'):
    added_files.append((str(db_file), '.'))

a = Analysis(
    ['desktop_app.py'],
    pathex=[r'{current_dir}'],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'werkzeug',
        'jinja2',
        'sqlalchemy',
        'sqlite3',
        'email.mime.text',  # Required for flask-mail
        'cefpython3',
        'importlib',
        'importlib.util',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Print debug info about what's being included
print("\\nIncluded data files:")
# Safe way to print data info without assuming structure
for item in a.datas:
    print(f"  {{item}}")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AMRSMaintenanceTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to True for debugging, change to False for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AMRSMaintenanceTracker',
)
"""
    
    # Write spec file
    spec_path = os.path.join(current_dir, "AMRSMaintenanceTracker.spec")
    with open(spec_path, "w") as f:
        f.write(spec_content)
    
    print(f"Created spec file: {spec_path}")
    return spec_path

def build_application(spec_file):
    """Build the application using the custom spec file"""
    print("\nBuilding application...")
    cmd = [sys.executable, "-m", "PyInstaller", spec_file, "--noconfirm"]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\nBuild completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with exit code: {e.returncode}")
        return False

def main():
    print("=" * 80)
    print("Building AMRS Maintenance Tracker with CEF Python")
    print("=" * 80)
    
    # First, apply the patch to CEF Python
    if not apply_cef_python_patch():
        print("\nFailed to patch CEF Python. Build may fail due to Python 3.10 incompatibility.")
        proceed = input("Do you want to continue anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Build cancelled.")
            return 1
    
    # Clean previous build artifacts
    clean_build_directories()
    
    # Create custom spec file
    spec_file = create_spec_file()
    
    # Build application
    success = build_application(spec_file)
    
    if success:
        output_dir = os.path.abspath("dist/AMRSMaintenanceTracker")
        print("\n" + "=" * 80)
        print(f"Application built successfully!")
        print(f"Output directory: {output_dir}")
        print(f"Run the application by executing: {os.path.join(output_dir, 'AMRSMaintenanceTracker.exe')}")
        print("=" * 80)
        return 0
    else:
        print("\n" + "=" * 80)
        print("Build failed.")
        print("For debugging, try building with console output:")
        print("  1. Edit the spec file to change 'console=False' to 'console=True'")
        print("  2. Run: python -m PyInstaller AMRSMaintenanceTracker.spec")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
