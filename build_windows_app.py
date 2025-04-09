"""
Self-Contained Windows Desktop Application Builder for AMRS Maintenance System
This script builds a fully standalone Windows executable that never requires a web browser
and bundles all necessary dependencies inside the executable.
"""
import os
import sys
import subprocess
import shutil
import time
import tempfile
import platform
from pathlib import Path

# Check if running on Windows
is_windows = platform.system() == 'Windows'
if not is_windows:
    print("⚠️ WARNING: This script is designed to build Windows applications.")
    print("   Running on non-Windows platforms may cause build failures.")
    print("   For best results, run this script on Windows.\n")
    user_input = input("Do you want to continue anyway? (y/n): ")
    if user_input.lower() != 'y':
        print("Build cancelled.")
        sys.exit(0)
    print("\nContinuing with build on non-Windows platform...\n")

# Windows-specific dependency checks and setup
def setup_windows_environment():
    """Set up Windows-specific environment for build success"""
    if not is_windows:
        return False
        
    success = True
    print("\n[WINDOWS SETUP] Checking Windows-specific requirements...")
    
    # Check Python architecture (should be 64-bit for best compatibility)
    is_64bit = sys.maxsize > 2**32
    print(f"[WINDOWS SETUP] Python architecture: {'64-bit' if is_64bit else '32-bit'}")
    if not is_64bit:
        print("[WINDOWS SETUP] ⚠️ Warning: Using 32-bit Python. 64-bit is recommended for better compatibility.")
        print("                Consider reinstalling Python (64-bit) for better results.")
    
    # Check for long path support
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem") as key:
            value, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
            if value == 1:
                print("[WINDOWS SETUP] ✓ Long path support is enabled")
            else:
                print("[WINDOWS SETUP] ⚠️ Long path support is not enabled. This might cause issues with deep paths.")
                print("                Run 'Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux'")
                print("                in an admin PowerShell to enable it.")
    except:
        print("[WINDOWS SETUP] Could not check long path support")
    
    # Check for Visual C++ Redistributable
    print("[WINDOWS SETUP] Checking for Microsoft Visual C++ Redistributables...")
    vcredist_installed = False
    try:
        # Simple check - try to list installed packages and grep for Visual C++
        result = subprocess.run(
            'powershell "Get-WmiObject -Class Win32_Product | Select-String -Pattern \'Visual C\+\+ Redistributable\'"',
            capture_output=True, text=True, shell=True
        )
        if "Visual C++" in result.stdout:
            print("[WINDOWS SETUP] ✓ Visual C++ Redistributable appears to be installed")
            vcredist_installed = True
        else:
            print("[WINDOWS SETUP] ⚠️ Visual C++ Redistributable may not be installed")
            print("                Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe")
            success = False
    except:
        print("[WINDOWS SETUP] Could not check for Visual C++ Redistributable")
    
    # Clean up temporary folders that might cause issues
    print("[WINDOWS SETUP] Cleaning temporary build directories...")
    temp_dirs_to_clean = [
        os.path.join(tempfile.gettempdir(), "pip-build-env-*"),
        os.path.join(tempfile.gettempdir(), "pip-req-build-*"),
        os.path.join(tempfile.gettempdir(), "pip-install-*"),
    ]
    
    import glob
    for pattern in temp_dirs_to_clean:
        for dir_path in glob.glob(pattern):
            try:
                if os.path.isdir(dir_path):
                    print(f"[WINDOWS SETUP] Cleaning: {dir_path}")
                    shutil.rmtree(dir_path, ignore_errors=True)
            except:
                pass
    
    return success

# Windows-specific dependency versions known to work well together
WINDOWS_DEPS = {
    "pyinstaller": ["pyinstaller==5.13.0", "pyinstaller==5.8.0", "pyinstaller==5.6.2"],
    "pyqt": ["PyQt5==5.15.7", "PyQt5==5.15.6", "PyQt5==5.15.2"],
    "webengine": ["PyQtWebEngine==5.15.6", "PyQtWebEngine==5.15.5", "PyQtWebEngine==5.15.2"],
    "pillow": ["Pillow==10.0.0", "Pillow==9.5.0", "Pillow==9.0.0"],
}

# Run Windows setup before proceeding with installation
if is_windows:
    setup_windows_environment()

# Configuration
APP_NAME = "AMRS Maintenance Tracker"
APP_VERSION = "1.0.0"
SERVER_URL = "https://amrs-preventative-maintenance.onrender.com"
OUTPUT_DIR = "dist"
BUILD_DIR = "build"
MAIN_SCRIPT = "amrs_standalone.py"
ICON_FILE = "amrs_icon.ico"
SPLASH_FILE = "splash.png"

print(f"Building {APP_NAME} v{APP_VERSION}")
print(f"This application will connect to: {SERVER_URL}")
print("-" * 60)

# Create output directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BUILD_DIR, exist_ok=True)

# Create simple icon file if it doesn't exist
if not os.path.exists(ICON_FILE):
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple orange square icon
        img = Image.new('RGB', (256, 256), color = (254, 121, 0))
        d = ImageDraw.Draw(img)
        d.rectangle((50, 50, 206, 206), fill=(255, 255, 255))
        d.text((70, 120), "AMRS", fill=(254, 121, 0), font_size=48)
        
        # Save in multiple formats
        img.save(ICON_FILE)
        img.save(SPLASH_FILE)
        print(f"Created icon file: {ICON_FILE}")
    except Exception as e:
        print(f"Could not create icon: {str(e)} - continuing without icon")

# Improved dependency installation with better error handling
print("Installing required dependencies for build...")

# Function to run pip with robust error handling
def install_package(package_name, alternatives=None):
    """Install a package with pip, trying alternatives if the first attempt fails"""
    print(f"Installing {package_name}...")
    
    # For Windows, try using --no-cache-dir to avoid cache-related issues
    pip_extra_args = ["--no-cache-dir"] if is_windows else []
    
    # First try direct installation
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name] + pip_extra_args,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"× Failed to install {package_name}: {e}")
        if e.stderr:
            print(f"  Error output: {e.stderr.strip()}")
        
        # If alternatives exist, try them one by one
        if alternatives:
            print(f"  Trying alternative packages for {package_name}...")
            for alt in alternatives:
                try:
                    print(f"  Trying alternative: {alt}")
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", alt] + pip_extra_args,
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    print(f"  ✓ Successfully installed alternative package {alt}")
                    return True
                except subprocess.CalledProcessError as alt_e:
                    print(f"  × Failed to install alternative {alt}")
                    if alt_e.stderr and "Microsoft Visual C++" in alt_e.stderr:
                        print("\n⚠️ Visual C++ build tools are required.")
                        print("Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
                        print("During installation, select 'Desktop development with C++'\n")
                    continue
        
        print(f"× All installation attempts for {package_name} failed")
        return False

# Dictionary to track what UI toolkits are available
ui_toolkit = {
    "qt5": False,
    "qt6": False,
    "tkinter": True,  # Tkinter is part of standard library and assumed available
}

# First install base build tools with Windows-specific versions
install_package("pyinstaller>=5.0.0", WINDOWS_DEPS["pyinstaller"])

# Try installing PyQt5 with Windows-specific fallbacks
qt5_success = install_package("pyqt5", WINDOWS_DEPS["pyqt"])
if qt5_success:
    ui_toolkit["qt5"] = True
    # Install QtWebEngine component with Windows-specific versions
    webengine_success = install_package("PyQtWebEngine", WINDOWS_DEPS["webengine"])
    if not webengine_success:
        print("⚠️ Warning: PyQtWebEngine failed to install. Web functionality will be limited.")

# If PyQt5 failed, try PyQt6
if not ui_toolkit["qt5"]:
    qt6_success = install_package("pyqt6", ["PyQt6==6.5.0", "PyQt6==6.4.0"])
    if qt6_success:
        ui_toolkit["qt6"] = True
        # Install QtWebEngine component for Qt6
        webengine6_success = install_package("PyQt6-WebEngine", ["PyQt6-WebEngine==6.5.0", "PyQt6-WebEngine==6.4.0"])
        if not webengine6_success:
            print("⚠️ Warning: PyQt6-WebEngine failed to install. Web functionality will be limited.")

# Install Pillow for icon generation but don't fail if not available
pillow_available = install_package("pillow", ["Pillow==10.0.0", "Pillow==9.5.0"])

print("\nDependency installation summary:")
print(f"PyQt5:          {'✓ Available' if ui_toolkit['qt5'] else '× Not available'}")
print(f"PyQt6:          {'✓ Available' if ui_toolkit['qt6'] else '× Not available'}")
print(f"Tkinter:        {'✓ Available' if ui_toolkit['tkinter'] else '× Not available'}")
print(f"Pillow:         {'✓ Available' if pillow_available else '× Not available'}")

# Create a standalone application with embedded browser - MODIFIED for toolkit detection
print(f"Creating standalone application: {MAIN_SCRIPT}")

# Use a different approach to writing the file content to avoid syntax issues
# Build complete strings for each section then write them all at once

# Basic imports
basic_imports = """
import os
import sys
import time
import sqlite3
import threading
import datetime
import traceback
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
"""

# UI toolkit imports based on availability
qt5_imports = """
# Using PyQt5 for UI
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    try:
        from PyQt5.QtWebEngineWidgets import *
        WEB_ENGINE_AVAILABLE = True
    except ImportError:
        WEB_ENGINE_AVAILABLE = False
    
    USING_QT5 = True
    USING_QT6 = False
    USING_TKINTER = False
except ImportError:
    USING_QT5 = False
"""

qt6_imports = """
# Using PyQt6 for UI
try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
    try:
        from PyQt6.QtWebEngineWidgets import *
        from PyQt6.QtWebEngineCore import *
        WEB_ENGINE_AVAILABLE = True
    except ImportError:
        WEB_ENGINE_AVAILABLE = False
    
    USING_QT5 = False
    USING_QT6 = True
    USING_TKINTER = False
except ImportError:
    USING_QT6 = False
"""

no_qt_imports = """
# PyQt not available
USING_QT5 = False
USING_QT6 = False
WEB_ENGINE_AVAILABLE = False
"""

tkinter_imports = """
# Try Tkinter
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, font
    from tkinter.scrolledtext import ScrolledText
    USING_TKINTER = True
except ImportError:
    USING_TKINTER = False
"""

# App configuration
app_config = f"""
# Application configuration
APP_NAME = "{APP_NAME}"
APP_VERSION = "{APP_VERSION}"
SERVER_URL = "{SERVER_URL}"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".amrs-maintenance")
DB_PATH = os.path.join(CACHE_DIR, "offline_data.db")

# Create cache directory
os.makedirs(CACHE_DIR, exist_ok=True)

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(CACHE_DIR, 'app.log')),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# Log what UI toolkit we're using
if USING_QT5:
    log.info("Using PyQt5 UI toolkit")
    if WEB_ENGINE_AVAILABLE:
        log.info("QtWebEngine is available")
    else:
        log.info("QtWebEngine is not available - using simple browser")
elif USING_QT6:
    log.info("Using PyQt6 UI toolkit")
    if WEB_ENGINE_AVAILABLE:
        log.info("QtWebEngine is available")
    else:
        log.info("QtWebEngine is not available - using simple browser")
elif USING_TKINTER:
    log.info("Using Tkinter UI toolkit - limited functionality")
else:
    log.error("No UI toolkit available - cannot continue")
"""

# Offline manager class - fixed the nested docstring issue
offline_manager = """
# ===== OFFLINE DATABASE MANAGER =====
class OfflineManager:
    '''Manages local data storage and server synchronization'''
    
    def __init__(self):
        self.server_url = SERVER_URL
        self.init_db()
        
    def init_db(self):
        '''Initialize SQLite database tables'''
        try:
            log.info(f"Initializing offline database at {DB_PATH}")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Create basic tables
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_pages (
                url TEXT PRIMARY KEY,
                content TEXT,
                content_type TEXT,
                timestamp INTEGER
            )''')
            
            conn.commit()
            conn.close()
            log.info("Database initialization complete")
        except Exception as e:
            log.error(f"Database initialization error: {e}")
            log.error(traceback.format_exc())
            
    def is_online(self):
        '''Check if server is reachable'''
        try:
            with urlopen(f"{self.server_url}/health", timeout=3) as response:
                return response.getcode() == 200
        except:
            return False
"""

# Main entry point
main_code = r"""
# Main entry point
if __name__ == "__main__":
    try:
        log.info(f"Starting {APP_NAME} v{APP_VERSION}")
        log.info(f"Server URL: {SERVER_URL}")
        
        # Initialize offline manager
        offline_manager = OfflineManager()
        
        # Check connection
        is_online = offline_manager.is_online()
        log.info(f"Server connection: {'Online' if is_online else 'Offline'}")
        
        # Start UI based on what's available
        if USING_QT5 or USING_QT6:
            # Use PyQt interface
            app = QApplication(sys.argv)
            
            # Basic window with status message
            window = QMainWindow()
            window.setWindowTitle(APP_NAME)
            window.resize(800, 600)
            
            central_widget = QWidget()
            window.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            
            status_label = QLabel(f"Connected to {SERVER_URL}" if is_online else "Offline Mode")
            layout.addWidget(status_label)
            
            # Add a simple browser if available
            if WEB_ENGINE_AVAILABLE:
                browser = QWebEngineView()
                browser.load(QUrl(SERVER_URL))
                layout.addWidget(browser)
                
                if not is_online:
                    browser.setHtml(f"<h1>Offline Mode</h1><p>Could not connect to {SERVER_URL}</p>")
            else:
                info_label = QLabel("WebEngine not available - simple mode only")
                layout.addWidget(info_label)
            
            window.show()
            sys.exit(app.exec_() if USING_QT5 else app.exec())
            
        elif USING_TKINTER:
            # Use Tkinter fallback
            root = tk.Tk()
            root.title(APP_NAME)
            root.geometry("800x600")
            
            label = tk.Label(root, text=f"Connected to {SERVER_URL}" if is_online else "Offline Mode")
            label.pack(pady=20)
            
            text = ScrolledText(root)
            text.pack(fill=tk.BOTH, expand=True)
            text.insert(tk.END, f"AMRS Maintenance Tracker v{APP_VERSION}\n\n")
            text.insert(tk.END, f"Server URL: {SERVER_URL}\n")
            text.insert(tk.END, f"Connection Status: {'Online' if is_online else 'Offline'}\n\n")
            text.insert(tk.END, "WebEngine not available with Tkinter - basic functionality only\n")
            
            root.mainloop()
        else:
            # No UI toolkit available
            log.error("No UI toolkit available - cannot start application")
            print(f"ERROR: No UI toolkit available. Application cannot start.")
            print(f"Please install PyQt5 or PyQt6 to run this application.")
    except Exception as e:
        # Show error message
        error_details = traceback.format_exc()
        log.critical(f"Fatal application error: {e}\n{error_details}")
        
        print(f"ERROR: {str(e)}")
        print(f"See log file: {os.path.join(CACHE_DIR, 'app.log')}")
"""

# Now write everything to the file at once
with open(MAIN_SCRIPT, "w", encoding="utf-8") as f:
    f.write(basic_imports)
    
    # Add UI toolkit imports based on availability
    if ui_toolkit.get("qt5", False):
        f.write(qt5_imports)
    elif ui_toolkit.get("qt6", False):
        f.write(qt6_imports)
    else:
        f.write(no_qt_imports)
    
    # Always add Tkinter as fallback
    f.write(tkinter_imports)
    
    # Add the rest of the code
    f.write(app_config)
    f.write(offline_manager)
    f.write(main_code)

print(f"Created {MAIN_SCRIPT}")

# Build with PyInstaller
print("\nBuilding executable with PyInstaller...")
try:
    # Create spec file with all dependencies
    spec_file = f"{os.path.splitext(MAIN_SCRIPT)[0]}.spec"
    
    with open(spec_file, "w") as f:
        f.write(f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtWebEngineWidgets',
                  'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtWebEngineWidgets',
                  'tkinter', 'sqlite3', 'logging', 'urllib', 'http.client'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add icon and splash image
if os.path.exists('{ICON_FILE}'):
    a.datas += [('{ICON_FILE}', '{ICON_FILE}', 'DATA')]
    
if os.path.exists('{SPLASH_FILE}'):
    a.datas += [('{SPLASH_FILE}', '{SPLASH_FILE}', 'DATA')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME.replace(" ", "")}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{ICON_FILE}' if os.path.exists('{ICON_FILE}') else None,
    version='file_version_info.txt',
)
""")
    
    # Create version info file
    with open("file_version_info.txt", "w") as f:
        f.write(f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({APP_VERSION.replace('.', ', ')}, 0),
    prodvers=({APP_VERSION.replace('.', ', ')}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'AMRS'),
        StringStruct(u'FileDescription', u'{APP_NAME}'),
        StringStruct(u'FileVersion', u'{APP_VERSION}'),
        StringStruct(u'InternalName', u'{APP_NAME}'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2023 AMRS'),
        StringStruct(u'OriginalFilename', u'{APP_NAME.replace(" ", "")}.exe'),
        StringStruct(u'ProductName', u'{APP_NAME}'),
        StringStruct(u'ProductVersion', u'{APP_VERSION}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
""")
    
    # Run PyInstaller with the spec file
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", spec_file],
        check=True
    )
    
    # Check if executable was created
    exe_path = os.path.join("dist", f"{APP_NAME.replace(' ', '')}.exe")
    if os.path.exists(exe_path):
        print(f"\n✅ Successfully built {exe_path}")
        
        # Copy to output directory if different
        if OUTPUT_DIR != "dist":
            shutil.copy(exe_path, os.path.join(OUTPUT_DIR, os.path.basename(exe_path)))
            print(f"Copied to {os.path.join(OUTPUT_DIR, os.path.basename(exe_path))}")
    else:
        print(f"\n❌ Failed to create executable at {exe_path}")
        
except Exception as e:
    print(f"\n❌ PyInstaller build failed: {e}")
    print("Check logs for details.")

print("\n" + "=" * 60)
print(f"Build process complete for {APP_NAME} v{APP_VERSION}")
print(f"The application will connect to: {SERVER_URL}")
print(f"Executable should be located in: {os.path.abspath(OUTPUT_DIR)}")
print("=" * 60)