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

# Create a standalone application with embedded browser
print(f"Creating standalone application: {MAIN_SCRIPT}")

# Write the Python code to the standalone script file in chunks to avoid nested docstring issues
with open(MAIN_SCRIPT, "w", encoding="utf-8") as f:
    # Write imports and basic setup
    f.write("""
import os
import sys
import time
import json
import sqlite3
import threading
import datetime
import uuid
import tempfile
import base64
import io
import re
import traceback
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from http.client import HTTPResponse

# Try to import UI libraries
try:
    # First try PyQt5
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWebEngineWidgets import *
    USING_QT5 = True
    USING_QT6 = False
    USING_TKINTER = False
except ImportError:
    try:
        # Next try PyQt6
        from PyQt6.QtWidgets import *
        from PyQt6.QtCore import *
        from PyQt6.QtGui import *
        from PyQt6.QtWebEngineWidgets import *
        from PyQt6.QtWebEngineCore import *
        USING_QT5 = False
        USING_QT6 = True
        USING_TKINTER = False
    except ImportError:
        # Last resort, fall back to tkinter
        import tkinter as tk
        from tkinter import ttk, messagebox, font
        from tkinter.scrolledtext import ScrolledText
        USING_QT5 = False
        USING_QT6 = False
        USING_TKINTER = True

# Application configuration
""")

    # Write configuration variables
    f.write(f'APP_NAME = "{APP_NAME}"\n')
    f.write(f'APP_VERSION = "{APP_VERSION}"\n')
    f.write(f'SERVER_URL = "{SERVER_URL}"\n')
    f.write('CACHE_DIR = os.path.join(os.path.expanduser("~"), ".amrs-maintenance")\n')
    f.write('DB_PATH = os.path.join(CACHE_DIR, "offline_data.db")\n\n')

    # Continue with more setup
    f.write("""
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

# ===== OFFLINE DATABASE MANAGER =====
class OfflineManager:
    '''Manages local data storage and server synchronization'''
    
    def __init__(self):
        self.server_url = SERVER_URL
        self.init_db()
""")

    # Write the rest of the OfflineManager class without docstrings using triple quotes
    f.write("""        
    def init_db(self):
        '''Initialize SQLite database tables'''
        try:
            log.info(f"Initializing offline database at {DB_PATH}")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Table for cached pages
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_pages (
                url TEXT PRIMARY KEY,
                content TEXT,
                content_type TEXT,
                timestamp INTEGER
            )''')
            
            # Rest of database initialization
            # ...
""")
    
    # Continue writing the rest of the file in chunks, avoiding nested triple quotes when possible

    # Write the PyQt application class
    f.write("""
# ===== QT APPLICATION (PYQT5/6) =====
class StandaloneQtApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.offline_manager = OfflineManager()
""")
    
    # Write icon file paths
    f.write(f"""
        # Set application details
        if USING_QT5:
            self.app.setApplicationName(APP_NAME)
            self.app.setApplicationVersion(APP_VERSION)
            self.app.setWindowIcon(QIcon("{ICON_FILE}") if os.path.exists("{ICON_FILE}") else QIcon())
        elif USING_QT6:
            self.app.setApplicationName(APP_NAME)
            self.app.setApplicationVersion(APP_VERSION)
            self.app.setWindowIcon(QIcon("{ICON_FILE}") if os.path.exists("{ICON_FILE}") else QIcon())
            
        # Create splash screen if file exists
        self.show_splash_screen()
""")

    # Continue with the rest of the application code
    f.write("""
    def show_splash_screen(self):
        '''Show splash screen while app is loading'''
""")

    # Write the rest of your application code in similar chunks
    # End with the main entry point

    f.write("""
# Main entry point
if __name__ == "__main__":
    try:
        # Start the appropriate UI
        if USING_QT5 or USING_QT6:
            # Use Qt interface
            log.info("Starting Qt application")
            StandaloneQtApp()
        elif USING_TKINTER:
            # Use Tkinter fallback
            log.info("Starting Tkinter application")
            StandaloneTkApp()
        else:
            # If this happens, we've hit an impossible state
            raise RuntimeError("No suitable UI framework available")
    except Exception as e:
        # Show error message
        error_details = traceback.format_exc()
        log.critical(f"Fatal application error: {e}\\n{error_details}")
        
        # Try to display error message to user
        # ...
""")

print(f"Created {MAIN_SCRIPT}")

# Try to install necessary dependencies for build
print("Installing required dependencies for build...")
try:
    # Install PyInstaller if not already installed
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Try installing PyQt5 for better UI
    try:
        print("Installing PyQt5...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "PyQt5", "PyQtWebEngine"],
            check=True
        )
        print("Successfully installed PyQt5")
    except:
        print("Could not install PyQt5")
        
    # Install Pillow for icon creation
    try:
        print("Installing Pillow for icon creation...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "Pillow"],
            check=True
        )
        print("Successfully installed Pillow")
    except:
        print("Could not install Pillow - continuing without custom icon")
        
except Exception as e:
    print(f"Error installing dependencies: {e}")
    print("Continuing with available packages...")

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