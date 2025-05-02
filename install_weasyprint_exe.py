import os
import shutil
import sys

print("[WeasyPrint Installer] Starting installation...")

# Path to your packaged resources directory
RESOURCES_DIR = os.path.join(os.path.dirname(__file__), 'dist', 'win-unpacked', 'resources')
# Path to Python Scripts directory in packaged app
VENV_SCRIPTS = os.path.join(RESOURCES_DIR, 'venv', 'Scripts')
# Path to local bin directory with weasyprint.exe
LOCAL_BIN_DIR = os.path.join(os.path.dirname(__file__), 'dependencies', 'bin')
# Target location for weasyprint.exe in the packaged app
TARGET_BIN_DIR = os.path.join(RESOURCES_DIR, 'bin')

# Create necessary directories
os.makedirs(VENV_SCRIPTS, exist_ok=True)
os.makedirs(TARGET_BIN_DIR, exist_ok=True)

# Check for weasyprint.exe in local bin directory
weasyprint_exe = os.path.join(LOCAL_BIN_DIR, 'weasyprint.exe')
if os.path.exists(weasyprint_exe):
    print(f"[WeasyPrint Installer] Found weasyprint.exe at {weasyprint_exe}")
    # Copy weasyprint.exe to the bin directory in the packaged app
    target_exe = os.path.join(TARGET_BIN_DIR, 'weasyprint.exe')
    print(f"[WeasyPrint Installer] Copying weasyprint.exe to {target_exe}")
    shutil.copy2(weasyprint_exe, target_exe)
    
    # Create a wrapper script in the Python Scripts directory that calls the exe
    wrapper_path = os.path.join(VENV_SCRIPTS, 'weasyprint.exe')
    print(f"[WeasyPrint Installer] Creating wrapper script at {wrapper_path}")
    
    # Create a simple batch file that forwards to the real executable
    with open(wrapper_path, 'w') as f:
        f.write(f'@echo off\r\n"{os.path.join(TARGET_BIN_DIR, "weasyprint.exe")}" %*')
    
    print("[WeasyPrint Installer] Installation completed successfully")
    sys.exit(0)

print("[WeasyPrint Installer] weasyprint.exe not found in dependencies/bin")
print("[WeasyPrint Installer] Please run setup_weasyprint_exe.py and copy weasyprint.exe to the dependencies/bin directory")
print("[WeasyPrint Installer] PDF generation may not work without this executable")

# Exit gracefully - we'll handle missing weasyprint.exe at runtime
print("[WeasyPrint Installer] Installation process completed with warnings")