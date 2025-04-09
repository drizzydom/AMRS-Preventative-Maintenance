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

# Windows-specific dependency versions - EXACTLY MATCHING PAIRS are crucial for WebEngine
WINDOWS_DEPS = {
    "pyinstaller": ["pyinstaller==5.13.0", "pyinstaller==5.8.0", "pyinstaller==5.6.2"],
    # These specific version combinations are known to work together well
    "pyqt_combos": [
        ("PyQt5==5.15.2", "PyQtWebEngine==5.15.2"),  # Best match combo
        ("PyQt5==5.15.6", "PyQtWebEngine==5.15.6"),  # Also works well
        ("PyQt5==5.15.7", "PyQtWebEngine==5.15.6"),  # Sometimes works
    ],
    "pillow": ["Pillow==10.0.0", "Pillow==9.5.0", "Pillow==9.0.0"],
    # Add dependencies for API and template-based approach
    "requests": ["requests==2.31.0", "requests==2.28.2"],
    "jinja2": ["Jinja2==3.1.2", "Jinja2==3.0.3"],
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

# Enhanced function to install PyQt and WebEngine as a matched pair
def install_qt_with_webengine():
    """Install PyQt and PyQtWebEngine as compatible pairs"""
    print("Installing PyQt with WebEngine components...")
    
    # First clean any existing installations that might conflict
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", "PyQt5", "PyQtWebEngine"],
            check=False,  # Don't fail if packages aren't installed
            capture_output=True
        )
        print("Cleaned existing PyQt installations")
    except:
        pass
        
    # Try each known working combination
    success = False
    for pyqt_ver, webengine_ver in WINDOWS_DEPS["pyqt_combos"]:
        try:
            print(f"\nTrying combination: {pyqt_ver} with {webengine_ver}")
            
            # Install PyQt first
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--no-cache-dir", pyqt_ver],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✓ Successfully installed {pyqt_ver}")
            
            # Then install matching WebEngine
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--no-cache-dir", webengine_ver],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✓ Successfully installed {webengine_ver}")
            
            # Test if imports work
            test_script = "import sys; from PyQt5.QtWidgets import QApplication; from PyQt5.QtWebEngineWidgets import QWebEngineView; print('WebEngine successfully installed and imported!')"
            result = subprocess.run(
                [sys.executable, "-c", test_script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✓ WebEngine TEST PASSED: Imports working correctly!")
                success = True
                break
            else:
                print("× WebEngine test failed despite installation succeeding")
                print(f"  Error: {result.stderr}")
                # Continue to the next combination
        except Exception as e:
            print(f"× Failed to install combination: {str(e)}")
            continue
    
    return success

# Dictionary to track what UI toolkits are available
ui_toolkit = {
    "qt5": False,
    "qt6": False,
    "tkinter": True,  # Tkinter is part of standard library and assumed available
}

# First install base build tools
install_package("pyinstaller>=5.0.0", WINDOWS_DEPS["pyinstaller"])

# Install API communication libraries
requests_available = install_package("requests", WINDOWS_DEPS["requests"])
jinja2_available = install_package("jinja2", WINDOWS_DEPS["jinja2"])

# Try installing PyQt with WebEngine as matched pairs
qt5_success = install_qt_with_webengine()
if qt5_success:
    ui_toolkit["qt5"] = True
    ui_toolkit["webengine"] = True
    print("✓ PyQt5 with WebEngine successfully installed")
else:
    print("× Could not install PyQt5 with WebEngine")
    # Try installing just PyQt5 without WebEngine
    qt5_basic_success = install_package("pyqt5", ["PyQt5==5.15.2", "PyQt5==5.15.6", "PyQt5==5.15.7"])
    if qt5_basic_success:
        ui_toolkit["qt5"] = True
        print("⚠️ PyQt5 installed but WebEngine failed - limited functionality")
    else:
        # Try Qt6 as fallback
        qt6_success = install_package("pyqt6", ["PyQt6==6.5.0", "PyQt6==6.4.0"])
        if qt6_success:
            ui_toolkit["qt6"] = True
            # Try WebEngine for Qt6
            webengine6_success = install_package("PyQt6-WebEngine", 
                                               ["PyQt6-WebEngine==6.5.0", "PyQt6-WebEngine==6.4.0"])
            if webengine6_success:
                ui_toolkit["webengine"] = True

# Install Pillow for icon generation but don't fail if not available
pillow_available = install_package("pillow", ["Pillow==10.0.0", "Pillow==9.5.0"])

print("\nDependency installation summary:")
print(f"PyQt5:          {'✓ Available' if ui_toolkit['qt5'] else '× Not available'}")
print(f"PyQt6:          {'✓ Available' if ui_toolkit['qt6'] else '× Not available'}")
print(f"Tkinter:        {'✓ Available' if ui_toolkit['tkinter'] else '× Not available'}")
print(f"Requests:       {'✓ Available' if requests_available else '× Not available'}")
print(f"Jinja2:         {'✓ Available' if jinja2_available else '× Not available'}")
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
        self.template_cache = {}
        self.load_templates()
        self.css_cache = {}
        self.load_css()
        
    def init_db(self):
        '''Initialize SQLite database tables'''
        try:
            log.info(f"Initializing offline database at {DB_PATH}")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Create basic tables
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_data (
                endpoint TEXT PRIMARY KEY,
                content TEXT,
                timestamp INTEGER
            )''')
            
            conn.commit()
            conn.close()
            log.info("Database initialization complete")
        except Exception as e:
            log.error(f"Database initialization error: {e}")
            log.error(traceback.format_exc())
    
    def load_templates(self):
        '''Load HTML templates from bundled files with comprehensive fallbacks'''
        log.info("Loading HTML templates...")
        
        # Define fallback templates that will be embedded in the code itself
        fallback_templates = {
            "dashboard.html": '''<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .header { background-color: #FE7900; color: white; padding: 10px; border-radius: 5px; }
        .card { border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-top: 20px; }
        .overdue { background-color: #ffeeee; border-left: 4px solid #cc0000; }
        .due-soon { background-color: #ffffee; border-left: 4px solid #cccc00; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Maintenance Dashboard (Embedded Template)</h1>
        <p>Connected to: {{server_url}}</p>
        <p>Status: {{status}}</p>
    </div>
    
    <div class="card overdue">
        <h2>Overdue Maintenance</h2>
        <table>
            <tr><th>Machine</th><th>Part</th><th>Days Overdue</th><th>Actions</th></tr>
            {% for item in overdue_items %}
            <tr>
                <td>{{item.machine}}</td>
                <td>{{item.part}}</td>
                <td>{{item.days}}</td>
                <td><button>Mark Complete</button></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <div class="card due-soon">
        <h2>Due Soon</h2>
        <table>
            <tr><th>Machine</th><th>Part</th><th>Days</th><th>Actions</th></tr>
            {% for item in due_soon_items %}
            <tr>
                <td>{{item.machine}}</td>
                <td>{{item.part}}</td>
                <td>{{item.days}}</td>
                <td><button>Mark Complete</button></td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>''',
            "maintenance.html": '''<!DOCTYPE html>
<html>
<head>
    <title>Record Maintenance</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .header { background-color: #FE7900; color: white; padding: 10px; border-radius: 5px; }
        .form { margin-top: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Record Maintenance (Embedded Template)</h1>
    </div>
    
    <div class="form">
        <div class="form-group">
            <label>Site:</label>
            <select>
                <option>Select Site</option>
                {% for site in sites %}
                <option>{{site.name}}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="form-group">
            <label>Machine:</label>
            <select><option>Select Machine</option></select>
        </div>
        
        <div class="form-group">
            <label>Part:</label>
            <select><option>Select Part</option></select>
        </div>
        
        <div class="form-group">
            <label>Date:</label>
            <input type="date">
        </div>
        
        <div class="form-group">
            <label>Comments:</label>
            <textarea rows="4"></textarea>
        </div>
        
        <button type="submit">Record Maintenance</button>
    </div>
</body>
</html>'''
        }
        
        # Try multiple approaches to find the templates
        templates_loaded = False
        
        try:
            # Approach 1: Look in standard locations relative to executable or script
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                base_dir = os.path.dirname(sys.executable)
                log.info(f"Running from PyInstaller bundle: {base_dir}")
                
                # Try multiple possible locations where PyInstaller might put the templates
                possible_dirs = [
                    os.path.join(base_dir, "embedded_templates"),
                    os.path.join(os.path.dirname(base_dir), "embedded_templates"),
                    base_dir,  # Sometimes files are extracted to the root directory
                ]
            else:
                # Running as script
                base_dir = os.path.dirname(os.path.abspath(__file__))
                log.info(f"Running from script: {base_dir}")
                
                possible_dirs = [
                    os.path.join(base_dir, "embedded_templates"),
                ]
            
            # Try to load from each possible directory
            for dir_path in possible_dirs:
                log.info(f"Looking for templates in: {dir_path}")
                
                for template_name, fallback_content in fallback_templates.items():
                    template_path = os.path.join(dir_path, template_name)
                    
                    if os.path.exists(template_path):
                        try:
                            with open(template_path, 'r', encoding='utf-8') as f:
                                self.template_cache[template_name] = f.read()
                                log.info(f"Successfully loaded template: {template_name} from {template_path}")
                                templates_loaded = True
                        except Exception as e:
                            log.error(f"Error reading template {template_path}: {e}")
            
            # Approach 2: Try to use PyInstaller's resource extraction (if running in frozen app)
            if not templates_loaded and getattr(sys, 'frozen', False):
                log.info("Trying PyInstaller-specific resource loading...")
                
                # First check if templates are directly in the _MEIPASS directory (PyInstaller temp dir)
                if hasattr(sys, '_MEIPASS'):
                    meipass_dir = sys._MEIPASS
                    log.info(f"MEIPASS directory: {meipass_dir}")
                    
                    for template_name in fallback_templates.keys():
                        # Try in root of _MEIPASS
                        template_path = os.path.join(meipass_dir, template_name)
                        if os.path.exists(template_path):
                            with open(template_path, 'r', encoding='utf-8') as f:
                                self.template_cache[template_name] = f.read()
                                log.info(f"Loaded from MEIPASS root: {template_name}")
                                templates_loaded = True
                                
                        # Try in embedded_templates subfolder of _MEIPASS  
                        template_path = os.path.join(meipass_dir, "embedded_templates", template_name)
                        if os.path.exists(template_path):
                            with open(template_path, 'r', encoding='utf-8') as f:
                                self.template_cache[template_name] = f.read()
                                log.info(f"Loaded from MEIPASS subfolder: {template_name}")
                                templates_loaded = True
                
                # Try loading as a resource directly via PyInstaller's pkg_resources approach
                try:
                    import pkg_resources
                    for template_name in fallback_templates.keys():
                        try:
                            resource_path = f"embedded_templates/{template_name}"
                            template_content = pkg_resources.resource_string(__name__, resource_path)
                            if template_content:
                                self.template_cache[template_name] = template_content.decode('utf-8')
                                log.info(f"Loaded via pkg_resources: {template_name}")
                                templates_loaded = True
                        except Exception as e:
                            log.debug(f"Could not load {template_name} via pkg_resources: {e}")
                except ImportError:
                    log.debug("pkg_resources not available")
            
            # Resort to embedded fallback templates if no files found
            if not templates_loaded:
                log.warning("Could not find external template files, using embedded fallbacks")
                self.template_cache = fallback_templates
                templates_loaded = True
        
        except Exception as e:
            log.error(f"Error during template loading: {e}")
            log.error(traceback.format_exc())
            
        # Final check - make sure we have templates one way or another
        if not templates_loaded:
            log.warning("Failed to load templates from any source, using fallbacks")
            self.template_cache = fallback_templates
            
        log.info(f"Loaded templates: {list(self.template_cache.keys())}")
    
    def load_css(self):
        '''Load CSS files for styling templates'''
        try:
            # Define embedded core CSS styles
            self.css_cache["core.css"] = '''
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f9fafb; }
                .header { background-color: #FE7900; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .header h1 { margin: 0; font-size: 24px; }
                .header p { margin: 5px 0 0 0; font-size: 14px; }
                
                .card { background-color: #fff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                       padding: 20px; margin-bottom: 20px; }
                
                .overdue { border-left: 5px solid #ef4444; }
                .due-soon { border-left: 5px solid #f59e0b; }
                .status-ok { border-left: 5px solid #10b981; }
                
                table { width: 100%; border-collapse: collapse; font-size: 14px; margin: 15px 0; }
                table, th, td { border: 1px solid #e5e7eb; }
                th { background-color: #f9fafb; font-weight: 600; text-align: left; padding: 12px; }
                td { padding: 12px; }
                tr:nth-child(even) { background-color: #f9fafb; }
                
                button, .btn { 
                    background-color: #FE7900; 
                    color: white; 
                    border: none; 
                    padding: 8px 16px; 
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background-color 0.2s;
                }
                button:hover, .btn:hover { background-color: #e56c00; }
                
                select, input, textarea {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    box-sizing: border-box;
                    font-size: 14px;
                }
                
                .form-group { margin-bottom: 20px; }
                label { display: block; font-weight: 600; margin-bottom: 6px; }
                
                .badge {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                }
                .badge-danger { background-color: #fee2e2; color: #ef4444; }
                .badge-warning { background-color: #fef3c7; color: #d97706; }
                .badge-success { background-color: #d1fae5; color: #10b981; }
            '''
            
            log.info("Loaded embedded CSS styles")
        except Exception as e:
            log.error(f"Error loading CSS: {e}")
    
    def get_css(self, name="core.css"):
        '''Get cached CSS by name'''
        return self.css_cache.get(name, "")
    
    def get_template(self, template_name):
        '''Get a template by name'''
        if template_name in self.template_cache:
            return self.template_cache[template_name]
        
        # Display a friendly error message if template is missing
        log.error(f"Template not found in cache: {template_name}")
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>Template Not Found</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; }}
        .error {{ color: #cc0000; }}
        .info {{ color: #666; margin-top: 20px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1 class="error">Template Not Found</h1>
    <p>The application could not find the template: <strong>{template_name}</strong></p>
    <p class="info">Please check the application log for more details.</p>
</body>
</html>'''
            
    def is_online(self):
        '''Check if server is reachable with improved reliability'''
        endpoints_to_try = [
            "/health",  # Standard health endpoint
            "/",        # Root path as fallback
            "/favicon.ico",  # Often accessible without auth
            "/static/favicon.ico" # Common path for favicons
        ]
        
        # Valid status codes for "online" state
        valid_status = [200, 201, 202, 203, 204, 301, 302, 307, 308]
        
        for endpoint in endpoints_to_try:
            try:
                url = f"{self.server_url}{endpoint}"
                headers = {
                    'User-Agent': f'AMRS-Maintenance-App/{APP_VERSION}',
                    'Accept': '*/*'
                }
                
                req = Request(url, headers=headers)
                with urlopen(req, timeout=3) as response:
                    status = response.getcode()
                    log.info(f"Connection check to {url}: status={status}")
                    if status in valid_status:
                        return True
            except Exception as e:
                log.debug(f"Connection check to {endpoint} failed: {str(e)}")
                continue
        
        log.warning("All connection attempts failed, considering offline")
        return False
            
    def cache_data(self, endpoint, content):
        '''Save data to cache'''
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            timestamp = int(time.time())
            
            cursor.execute(
                "INSERT OR REPLACE INTO cached_data (endpoint, content, timestamp) VALUES (?, ?, ?)",
                (endpoint, content, timestamp)
            )
            
            conn.commit()
            conn.close()
        except Exception as e:
            log.error(f"Error caching data: {e}")
            
    def get_cached_data(self, endpoint):
        '''Get cached data for an endpoint'''
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT content FROM cached_data WHERE endpoint = ?", (endpoint,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return row[0]
        except Exception as e:
            log.error(f"Error retrieving cached data: {e}")
            
        return None
"""

# Template renderer class
template_renderer = """
# ===== TEMPLATE RENDERER =====
class TemplateRenderer:
    '''Simple template rendering engine with CSS support'''
    
    def __init__(self, offline_manager):
        self.offline_manager = offline_manager
        
    def render(self, template_name, context=None):
        '''Render a template with the given context and embedded CSS'''
        if context is None:
            context = {}
            
        template = self.offline_manager.get_template(template_name)
        if not template:
            return f"<html><body><h1>Template {template_name} not found</h1></body></html>"
        
        # Get CSS styles
        css = self.offline_manager.get_css("core.css")
        
        # Inject CSS into template if not already there
        if "<style>" not in template:
            template = template.replace("</head>", f"<style>{css}</style></head>")
        
        # Handle standard variable substitution
        for key, value in context.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
            
        # Handle simple loops with {% for item in items %} ... {% endfor %}
        import re
        for match in re.finditer(r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}(.*?){%\s*endfor\s*%}', template, re.DOTALL):
            item_var, items_var, loop_content = match.groups()
            
            if items_var not in context or not isinstance(context[items_var], (list, tuple)):
                # Skip if items variable doesn't exist or isn't iterable
                template = template.replace(match.group(0), "")
                continue
                
            loop_items = []
            for item in context[items_var]:
                # Replace {{item.attribute}} with the actual value
                item_content = loop_content
                for key, value in item.items():
                    item_content = item_content.replace(f"{{{{{item_var}.{key}}}}}", str(value))
                loop_items.append(item_content)
                
            template = template.replace(match.group(0), ''.join(loop_items))
        
        # Return the fully rendered template
        return template
"""

# Add API client for fetching data without WebEngine
api_client = """
# ===== API CLIENT =====
class ApiClient:
    '''Client for interacting with the AMRS API'''
    
    def __init__(self):
        self.server_url = SERVER_URL
        self.offline_manager = OfflineManager()
        self.session_token = None
        
    def get(self, endpoint, use_cache=True):
        '''Make a GET request to the API with better error handling'''
        url = f"{self.server_url}/{endpoint.lstrip('/')}"
        
        try:
            # Check if we're online
            if not self.offline_manager.is_online():
                log.warning(f"Offline mode: retrieving cached data for {endpoint}")
                cached_data = self.offline_manager.get_cached_data(endpoint)
                if cached_data:
                    return cached_data
                else:
                    log.warning(f"No cached data available for {endpoint}")
                    return None
                
            # Make the request with proper headers
            headers = {
                'User-Agent': f'AMRS-Maintenance-App/{APP_VERSION}',
                'Accept': 'application/json, text/html'
            }
            
            if self.session_token:
                headers['Authorization'] = f"Bearer {self.session_token}"
                
            log.info(f"Making API request to {url}")
            req = Request(url, headers=headers)
            with urlopen(req, timeout=5) as response:
                content = response.read().decode('utf-8')
                status_code = response.getcode()
                
                log.info(f"API response: status={status_code}, length={len(content) if content else 0}")
                
                # Cache the response if successful
                if use_cache and response.getcode() == 200:
                    self.offline_manager.cache_data(endpoint, content)
                    
                return content
        except HTTPError as e:
            log.error(f"HTTP error ({url}): {e.code} - {e.reason}")
            cached_data = self.offline_manager.get_cached_data(endpoint)
            return cached_data if cached_data else None
        except URLError as e:
            log.error(f"URL error ({url}): {e.reason}")
            cached_data = self.offline_manager.get_cached_data(endpoint)
            return cached_data if cached_data else None
        except Exception as e:
            log.error(f"API request error ({url}): {e}")
            cached_data = self.offline_manager.get_cached_data(endpoint)
            return cached_data if cached_data else None
            
    def login(self, username, password):
        '''Log in to the API'''
        # This is a simplified example - in real app would make actual login request
        log.info(f"Attempting to log in as {username}...")
        
        try:
            # For demo, simply check if we're online and consider it success
            if self.offline_manager.is_online():
                self.session_token = f"SAMPLE_TOKEN_{int(time.time())}"
                log.info("Login successful")
                return True
            else:
                log.warning("Cannot log in - offline mode")
                return False
        except Exception as e:
            log.error(f"Login error: {e}")
            return False
        
    def fetch_maintenance_items(self):
        '''Get maintenance items from API or cache'''
        try:
            # First check if we're online to determine which data source to use
            is_online = self.offline_manager.is_online()
            log.info(f"Fetching maintenance items (online={is_online})")
            
            # In a production app, we would get real data from the API:
            # result = self.get('/api/maintenance')
            # return json.loads(result) if result else {"overdue_items": [], "due_soon_items": [], "status": "error"}
            
            # For demo, return sample data with more realistic fields
            import json
            return json.loads('''{
                "overdue_items": [
                    {"id": 1, "machine": "Machine A", "part": "Belt", "days": 5, "due_date": "2023-10-15"},
                    {"id": 2, "machine": "Machine B", "part": "Filter", "days": 3, "due_date": "2023-10-17"},
                    {"id": 3, "machine": "Machine C", "part": "Pump", "days": 10, "due_date": "2023-10-10"}
                ],
                "due_soon_items": [
                    {"id": 4, "machine": "Machine C", "part": "Motor", "days": 2, "due_date": "2023-10-22"},
                    {"id": 5, "machine": "Machine A", "part": "Bearing", "days": 5, "due_date": "2023-10-25"},
                    {"id": 6, "machine": "Machine D", "part": "Valve", "days": 7, "due_date": "2023-10-27"}
                ],
                "status": "success",
                "online": true
            }''')
        except Exception as e:
            log.error(f"Error fetching maintenance items: {e}")
            return {
                "overdue_items": [],
                "due_soon_items": [],
                "status": "error",
                "online": self.offline_manager.is_online()
            }
"""

# Main entry point
main_code = r"""
# Main entry point
if __name__ == "__main__":
    try:
        log.info(f"Starting {APP_NAME} v{APP_VERSION}")
        log.info(f"Server URL: {SERVER_URL}")
        
        # Initialize core components
        offline_manager = OfflineManager()
        api_client = ApiClient()
        template_renderer = TemplateRenderer(offline_manager)
        
        # Check connection
        is_online = offline_manager.is_online()
        log.info(f"Server connection: {'Online' if is_online else 'Offline'}")
        
        # Start UI based on what's available
        if USING_QT5 or USING_QT6:
            # Use PyQt interface
            app = QApplication(sys.argv)
            
            # Set application style for a more modern look
            app.setStyle("Fusion")
            
            # Main window setup with better styling
            window = QMainWindow()
            window.setWindowTitle(APP_NAME)
            window.resize(1000, 700)
            
            central_widget = QWidget()
            window.setCentralWidget(central_widget)
            
            main_layout = QVBoxLayout(central_widget)
            
            # Create tabs for different screens
            tabs = QTabWidget()
            main_layout.addWidget(tabs)
            
            # Dashboard tab
            dashboard_tab = QWidget()
            dashboard_layout = QVBoxLayout(dashboard_tab)
            
            # Dashboard header with improved styling
            header_layout = QHBoxLayout()
            status_label = QLabel(f"Connected to {SERVER_URL}" if is_online else "Offline Mode")
            status_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; "
                f"color: {'#1e7e34' if is_online else '#dc3545'};"
            )
            header_layout.addWidget(status_label)
            
            refresh_btn = QPushButton("Refresh Data")
            refresh_btn.setMaximumWidth(150)
            refresh_btn.setStyleSheet(
                "background-color: #FE7900; color: white; "
                "border: none; padding: 8px 16px; border-radius: 4px;"
            )
            header_layout.addWidget(refresh_btn)
            header_layout.addStretch()
            
            dashboard_layout.addLayout(header_layout)
            
            # We'll use a QTextBrowser to display HTML content from templates
            text_browser = QTextBrowser()
            text_browser.setOpenExternalLinks(True)
            dashboard_layout.addWidget(text_browser)
            
            # Function to update the dashboard
            def update_dashboard():
                try:
                    # Check connection status first
                    is_online = offline_manager.is_online()
                    log.info(f"Refreshing dashboard (online={is_online})")
                    
                    # Update status label
                    status_label.setText(f"Connected to {SERVER_URL}" if is_online else "Offline Mode")
                    status_label.setStyleSheet(
                        "font-weight: bold; font-size: 14px; "
                        f"color: {'#1e7e34' if is_online else '#dc3545'};"
                    )
                    
                    # Get maintenance data (either from API or mock)
                    maintenance_data = api_client.fetch_maintenance_items()
                    
                    # Calculate counts for summary
                    overdue_count = len(maintenance_data.get('overdue_items', []))
                    due_soon_count = len(maintenance_data.get('due_soon_items', []))
                    on_schedule_count = 10 - (overdue_count + due_soon_count)  # Just for demo
                    
                    # Get the current time for "last updated" info
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Determine status class for CSS
                    status_class = "good" if is_online else "overdue"
                    
                    # Render the dashboard template with expanded context
                    context = {
                        'server_url': SERVER_URL,
                        'status': 'Online' if is_online else 'Offline',
                        'status_class': status_class,
                        'overdue_items': maintenance_data.get('overdue_items', []),
                        'due_soon_items': maintenance_data.get('due_soon_items', []),
                        'overdue_count': overdue_count,
                        'due_soon_count': due_soon_count,
                        'on_schedule_count': on_schedule_count,
                        'last_updated': now
                    }
                    
                    html_content = template_renderer.render('dashboard.html', context)
                    text_browser.setHtml(html_content)
                    
                    log.info("Dashboard updated successfully")
                    
                except Exception as e:
                    log.error(f"Error updating dashboard: {e}")
                    log.error(traceback.format_exc())
            
            # Connect refresh button
            refresh_btn.clicked.connect(update_dashboard)
            
            # Render initial dashboard
            update_dashboard()
            
            # Add dashboard to tabs
            tabs.addTab(dashboard_tab, "Dashboard")
            
            # Maintenance tab
            maintenance_tab = QWidget()
            maintenance_layout = QVBoxLayout(maintenance_tab)
            
            # Maintenance form (native controls since we can't use web forms)
            form_layout = QFormLayout()
            
            site_combo = QComboBox()
            site_combo.addItem("Site A")
            site_combo.addItem("Site B")
            form_layout.addRow("Site:", site_combo)
            
            machine_combo = QComboBox()
            machine_combo.addItem("Machine 1")
            machine_combo.addItem("Machine 2")
            form_layout.addRow("Machine:", machine_combo)
            
            part_combo = QComboBox()
            part_combo.addItem("Belt")
            part_combo.addItem("Filter")
            form_layout.addRow("Part:", part_combo)
            
            date_edit = QDateEdit(QDate.currentDate())
            form_layout.addRow("Date:", date_edit)
            
            comments = QTextEdit()
            comments.setMaximumHeight(100)
            form_layout.addRow("Comments:", comments)
            
            submit_btn = QPushButton("Record Maintenance")
            
            maintenance_layout.addLayout(form_layout)
            maintenance_layout.addWidget(submit_btn)
            maintenance_layout.addStretch()
            
            # Add maintenance tab to tabs
            tabs.addTab(maintenance_tab, "Record Maintenance")
            
            # Display the app window
            window.show()
            
            # Start the application event loop
            sys.exit(app.exec_() if USING_QT5 else app.exec())
        
        elif USING_TKINTER:
            # Tkinter fallback implementation
            root = tk.Tk()
            root.title(APP_NAME)
            root.geometry("900x700")
            
            # Create notebook for tabs
            notebook = ttk.Notebook(root)
            notebook.pack(fill=tk.BOTH, expand=True)
            
            # Dashboard tab with basic info
            dashboard_frame = ttk.Frame(notebook)
            notebook.add(dashboard_frame, text="Dashboard")
            
            # Status frame
            status_frame = ttk.Frame(dashboard_frame)
            status_frame.pack(fill=tk.X, padx=10, pady=10)
            
            status_label = ttk.Label(status_frame, 
                                   text=f"Connected to {SERVER_URL}" if is_online else "Offline Mode")
            status_label.pack(side=tk.LEFT, padx=5)
            
            refresh_btn = ttk.Button(status_frame, text="Refresh Data")
            refresh_btn.pack(side=tk.RIGHT, padx=5)
            
            # Text area for content
            content_text = ScrolledText(dashboard_frame)
            content_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Add some default content
            content_text.insert(tk.END, f"AMRS Maintenance Tracker v{APP_VERSION}\n\n")
            content_text.insert(tk.END, f"Server URL: {SERVER_URL}\n")
            content_text.insert(tk.END, f"Connection Status: {'Online' if is_online else 'Offline'}\n\n")
            
            if is_online:
                # Add sample maintenance items
                items = api_client.fetch_maintenance_items()
                
                content_text.insert(tk.END, "===== OVERDUE ITEMS =====\n")
                for item in items['overdue_items']:
                    content_text.insert(tk.END, f"{item['machine']}: {item['part']} - {item['days']} days overdue\n")
                content_text.insert(tk.END, "\n")
                
                content_text.insert(tk.END, "===== DUE SOON =====\n")
                for item in items['due_soon_items']:
                    content_text.insert(tk.END, f"{item['machine']}: {item['part']} - Due in {item['days']} days\n")
            else:
                content_text.insert(tk.END, "Offline mode - using cached data\n")
                
            # Function to update dashboard
            def update_tkinter_dashboard():
                is_online = offline_manager.is_online()
                status_label.config(text=f"Connected to {SERVER_URL}" if is_online else "Offline Mode")
                
                content_text.delete(1.0, tk.END)
                content_text.insert(tk.END, f"AMRS Maintenance Tracker v{APP_VERSION}\n\n")
                content_text.insert(tk.END, f"Server URL: {SERVER_URL}\n")
                content_text.insert(tk.END, f"Connection Status: {'Online' if is_online else 'Offline'}\n\n")
                
                # Add maintenance items
                items = api_client.fetch_maintenance_items()
                
                content_text.insert(tk.END, "===== OVERDUE ITEMS =====\n")
                for item in items['overdue_items']:
                    content_text.insert(tk.END, f"{item['machine']}: {item['part']} - {item['days']} days overdue\n")
                content_text.insert(tk.END, "\n")
                
                content_text.insert(tk.END, "===== DUE SOON =====\n")
                for item in items['due_soon_items']:
                    content_text.insert(tk.END, f"{item['machine']}: {item['part']} - Due in {item['days']} days\n")
            
            # Connect refresh button
            refresh_btn.config(command=update_tkinter_dashboard)
            
            # Maintenance tab
            maintenance_frame = ttk.Frame(notebook)
            notebook.add(maintenance_frame, text="Record Maintenance")
            
            # Simple maintenance form
            form_frame = ttk.LabelFrame(maintenance_frame, text="Record Maintenance")
            form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            ttk.Label(form_frame, text="Site:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            site_combo = ttk.Combobox(form_frame, values=["Site A", "Site B"])
            site_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
            
            ttk.Label(form_frame, text="Machine:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            machine_combo = ttk.Combobox(form_frame, values=["Machine 1", "Machine 2"])
            machine_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
            
            ttk.Label(form_frame, text="Part:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
            part_combo = ttk.Combobox(form_frame, values=["Belt", "Filter"])
            part_combo.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
            
            ttk.Label(form_frame, text="Comments:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
            comments = ScrolledText(form_frame, height=5)
            comments.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
            
            submit_btn = ttk.Button(form_frame, text="Record Maintenance")
            submit_btn.grid(row=4, column=0, columnspan=2, pady=10)
            
            # Configure grid weights
            form_frame.columnconfigure(1, weight=1)
            
            # Start the Tkinter main loop
            root.mainloop()
            
        else:
            # No UI toolkit available
            log.error("No UI toolkit available - cannot start application")
            print(f"ERROR: No UI toolkit available. Application cannot start.")
            print(f"Please install PyQt5, PyQt6, or ensure Tkinter is available.")
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
    f.write(api_client)       # Add new API client
    f.write(template_renderer) # Add new template renderer
    f.write(main_code)

print(f"Created {MAIN_SCRIPT}")

# Create templates directory in the executable
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "embedded_templates")
os.makedirs(templates_dir, exist_ok=True)

print(f"Creating templates directory: {templates_dir}")

# Create example embedded templates
dashboard_template = os.path.join(templates_dir, "dashboard.html")
maintenance_template = os.path.join(templates_dir, "maintenance.html")

print(f"Writing dashboard template to: {dashboard_template}")
with open(dashboard_template, "w", encoding="utf-8") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .header { background-color: #FE7900; color: white; padding: 10px; border-radius: 5px; }
        .card { border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-top: 20px; }
        .overdue { background-color: #ffeeee; border-left: 4px solid #cc0000; }
        .due-soon { background-color: #ffffee; border-left: 4px solid #cccc00; }
        .status-ok { background-color: #eeffee; border-left: 4px solid #00cc00; }
        table { width: 100%; border-collapse: collapse; }
        table, th, td { border: 1px solid #ddd; }
        th, td { padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Maintenance Dashboard</h1>
        <p>Connected to: {{server_url}}</p>
        <p>Status: {{status}}</p>
    </div>
    
    <div class="card overdue">
        <h2>Overdue Maintenance</h2>
        <table>
            <tr>
                <th>Machine</th>
                <th>Part</th>
                <th>Days Overdue</th>
                <th>Actions</th>
            </tr>
            {% for item in overdue_items %}
            <tr>
                <td>{{item.machine}}</td>
                <td>{{item.part}}</td>
                <td><span class="status-badge overdue">{{item.days}} days</span></td>
                <td>{{item.due_date}}</td>
                <td><button class="btn btn-sm" data-id="{{item.id}}">Mark Complete</button></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <div class="card due-soon">
        <h2>Due Soon</h2>
        <table>
            <tr>
                <th>Machine</th>
                <th>Part</th>
                <th>Due In</th>
                <th>Due Date</th>
                <th>Actions</th>
            </tr>
            {% for item in due_soon_items %}
            <tr>
                <td>{{item.machine}}</td>
                <td>{{item.part}}</td>
                <td><span class="status-badge warning">{{item.days}} days</span></td>
                <td>{{item.due_date}}</td>
                <td><button class="btn btn-sm" data-id="{{item.id}}">Mark Complete</button></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <div class="card">
        <h2>Last Updated: {{last_updated}}</h2>
        <p>Click the "Refresh Data" button above to check for new maintenance items.</p>
    </div>
</body>
</html>
""")

print(f"Writing maintenance template to: {maintenance_template}")
with open(maintenance_template, "w", encoding="utf-8") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Record Maintenance</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .header { background-color: #FE7900; color: white; padding: 10px; border-radius: 5px; }
        .form { margin-top: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        select, input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background-color: #FE7900; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Record Maintenance</h1>
    </div>
    
    <div class="form">
        <div class="form-group">
            <label for="site">Site:</label>
            <select id="site">
                <option value="">Select Site</option>
                {% for site in sites %}
                <option value="{{site.id}}">{{site.name}}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="form-group">
            <label for="machine">Machine:</label>
            <select id="machine">
                <option value="">Select Machine</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="part">Part:</label>
            <select id="part">
                <option value="">Select Part</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="date">Date:</label>
            <input type="date" id="date">
        </div>
        
        <div class="form-group">
            <label for="comments">Comments:</label>
            <textarea id="comments" rows="4"></textarea>
        </div>
        
        <button type="submit">Record Maintenance</button>
    </div>
</body>
</html>
""")

# Build with PyInstaller
print("\nBuilding executable with PyInstaller...")
try:
    # Create spec file with all dependencies
    spec_file = f"{os.path.splitext(MAIN_SCRIPT)[0]}.spec"
    
    # Important: Correctly reference the embedded_templates for PyInstaller
    templates_dir_relative = os.path.relpath(templates_dir)
    
    print(f"Using templates directory: {templates_dir_relative}")
    print(f"Dashboard template exists: {os.path.exists(dashboard_template)}")
    print(f"Maintenance template exists: {os.path.exists(maintenance_template)}")
    
    with open(spec_file, "w") as f:
        f.write(f"""# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Explicitly list template files to include
template_files = [
    (r'{os.path.abspath(dashboard_template)}', 'embedded_templates'),
    (r'{os.path.abspath(maintenance_template)}', 'embedded_templates')
]

# Print template files for debugging
print(f"Template files to be included: {{template_files}}")

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=[],
    binaries=[],
    datas=template_files,
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

# Also explicitly include templates directory
a.datas += [(f'embedded_templates/dashboard.html', r'{os.path.abspath(dashboard_template)}', 'DATA')]
a.datas += [(f'embedded_templates/maintenance.html', r'{os.path.abspath(maintenance_template)}', 'DATA')]

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
    console=True,  # Changed to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{ICON_FILE}' if os.path.exists('{ICON_FILE}') else None,
    version='file_version_info.txt',
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