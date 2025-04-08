"""
Robust Windows Desktop Application Builder for AMRS Maintenance System
This script builds a standalone Windows executable that connects to the Render deployment.
It falls back to simpler methods if PyInstaller encounters issues.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import winreg
import ctypes

# Configuration
APP_NAME = "AMRS Maintenance Tracker"
APP_VERSION = "1.0.0"
SERVER_URL = "https://amrs-preventative-maintenance.onrender.com"
OUTPUT_DIR = "dist"
BUILD_DIR = "build"
MAIN_SCRIPT = "amrs_connect.py"
BATCH_FILE = os.path.join(OUTPUT_DIR, "AMRS_Launcher.bat")

print(f"Building {APP_NAME} v{APP_VERSION}")
print(f"This application will connect to: {SERVER_URL}")
print("-" * 60)

# Create output directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BUILD_DIR, exist_ok=True)

# Create a simple, dependency-free main application script
print(f"Creating main application script: {MAIN_SCRIPT}")
with open(MAIN_SCRIPT, "w", encoding="utf-8") as f:
    f.write(f"""
import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.error
import threading
import time
import winreg
import subprocess
from pathlib import Path

# Configuration
SERVER_URL = "{SERVER_URL}"
APP_NAME = "{APP_NAME}"
APP_VERSION = "{APP_VERSION}"

class StandaloneWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1024x768")
        self.minsize(800, 600)
        
        # Set icon if available
        try:
            icon_path = os.path.join(os.path.dirname(sys.executable), "amrs_icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass
        
        # Create menu bar
        self.create_menu()
        
        # Create status bar
        self.status_var = tk.StringVar(value="Starting...")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create browser frame
        try:
            # Try to import browser components - fallbacks in sequence
            browser_frame = None
            
            # Try CEFPython if available
            try:
                from cefpython3 import cefpython as cef
                browser_frame = self.create_cef_browser(cef)
                self.status_var.set("Using CEF Browser Engine")
            except ImportError:
                # Try tkinterweb if available
                try:
                    from tkinterweb import HtmlFrame
                    browser_frame = HtmlFrame(self)
                    browser_frame.load_website(SERVER_URL)
                    browser_frame.pack(fill=tk.BOTH, expand=True)
                    self.status_var.set("Using TkinterWeb Browser Engine")
                except ImportError:
                    # Fallback to basic mode
                    browser_frame = self.create_basic_view()
                    self.status_var.set("Using Basic Browser Mode")
            
            if browser_frame:
                self.browser_frame = browser_frame
        except Exception as e:
            self.status_var.set(f"Error initializing browser: {{str(e)}}")
            # Final fallback to basic mode
            self.browser_frame = self.create_basic_view()
    
    def create_menu(self):
        # Create menubar
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh", command=self.refresh_page)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Open in Browser", command=lambda: webbrowser.open(SERVER_URL))
        tools_menu.add_command(label="Run on Startup", command=self.toggle_run_on_startup)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_cef_browser(self, cef):
        # Initialize CEF
        sys.excepthook = cef.ExceptHook
        cef.Initialize()
        
        # Create browser frame
        browser_frame = tk.Frame(self)
        browser_frame.pack(fill=tk.BOTH, expand=True)
        
        # Get window info
        window_info = cef.WindowInfo()
        rect = [0, 0, browser_frame.winfo_width(), browser_frame.winfo_height()]
        window_info.SetAsChild(browser_frame.winfo_id(), rect)
        
        # Create browser
        browser = cef.CreateBrowserSync(window_info, url=SERVER_URL)
        
        # Set up bindings for resize
        def on_resize(event):
            if browser:
                width, height = event.width, event.height
                browser.SetBounds(0, 0, width, height)
                browser_frame.update()
        
        browser_frame.bind("<Configure>", on_resize)
        
        # Make sure CEF is shut down properly
        def on_closing():
            cef.QuitMessageLoop()
            cef.Shutdown()
            self.destroy()
        
        self.protocol("WM_DELETE_WINDOW", on_closing)
        
        return browser_frame
        
    def create_basic_view(self):
        """Create a fallback basic view that provides connection options"""
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, 
                               text=APP_NAME,
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Status frame
        status_frame = ttk.LabelFrame(frame, text="Server Status")
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.server_status_var = tk.StringVar(value="Checking connection...")
        server_status = ttk.Label(status_frame, textvariable=self.server_status_var, padding=10)
        server_status.pack(fill=tk.X)
        
        # Connection button
        connect_btn = ttk.Button(
            frame,
            text="Connect to Application in Browser",
            command=lambda: webbrowser.open(SERVER_URL)
        )
        connect_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Auto-connect 
        self.auto_connect_var = tk.BooleanVar(value=True)
        auto_connect_cb = ttk.Checkbutton(
            frame,
            text="Automatically open in browser on startup",
            variable=self.auto_connect_var
        )
        auto_connect_cb.pack(anchor=tk.W, pady=(0, 20))
        
        # Server info
        info_text = f"""
        This is a standalone application that connects to:
        {{SERVER_URL}}
        
        For the best experience, this application will open the 
        AMRS Preventative Maintenance system in your default web browser.
        """
        
        info_label = ttk.Label(frame, text=info_text, justify=tk.LEFT, wraplength=500)
        info_label.pack(fill=tk.BOTH, expand=True)
        
        # Start connection check
        threading.Thread(target=self.check_connection, daemon=True).start()
        
        # Auto-connect if enabled
        if self.auto_connect_var.get():
            self.after(1500, lambda: webbrowser.open(SERVER_URL))
            
        return frame
    
    def check_connection(self):
        """Check server connection status"""
        try:
            self.server_status_var.set("Checking server connection...")
            
            try:
                with urllib.request.urlopen(f"{{SERVER_URL}}/health", timeout=5) as response:
                    if response.status == 200:
                        self.server_status_var.set("Server is online!")
                    else:
                        self.server_status_var.set(f"Server responded with status: {{response.status}}")
            except urllib.error.URLError:
                self.server_status_var.set("Cannot connect to server")
            except Exception as e:
                self.server_status_var.set(f"Error: {{str(e)}}")
        except:
            # Ignore errors if variables don't exist
            pass
    
    def refresh_page(self):
        """Refresh the current page"""
        try:
            # Try to refresh in CEF
            if hasattr(self, 'browser'):
                self.browser.Reload()
            else:
                # Fallback to restarting the app
                self.status_var.set("Refreshing...")
                # Re-check connection
                threading.Thread(target=self.check_connection, daemon=True).start()
        except:
            self.status_var.set("Refresh failed")
    
    def toggle_run_on_startup(self):
        """Toggle whether app runs on Windows startup"""
        try:
            # Get the path to the executable
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                app_path = sys.executable
            else:
                # Running as script
                app_path = sys.argv[0]
                
            app_path = os.path.abspath(app_path)
            
            # Check if already in startup
            startup_enabled = self.is_in_startup(app_path)
            
            if startup_enabled:
                # Remove from startup
                self.remove_from_startup()
                messagebox.showinfo("Startup Disabled", 
                                   f"{{APP_NAME}} will no longer start automatically with Windows.")
            else:
                # Add to startup
                self.add_to_startup(app_path)
                messagebox.showinfo("Startup Enabled", 
                                   f"{{APP_NAME}} will now start automatically with Windows.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not configure startup: {{str(e)}}")
    
    def is_in_startup(self, app_path=None):
        """Check if app is set to run on startup"""
        try:
            # Open the registry key
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                0, winreg.KEY_READ
            )
            
            try:
                # Check if our app name exists
                value, _ = winreg.QueryValueEx(reg_key, APP_NAME)
                return True
            except WindowsError:
                return False
            finally:
                winreg.CloseKey(reg_key)
        except:
            # Alternative method - check startup folder
            startup_folder = self.get_startup_folder()
            shortcut_path = os.path.join(startup_folder, f"{{APP_NAME}}.lnk")
            return os.path.exists(shortcut_path)
    
    def add_to_startup(self, app_path):
        """Add app to Windows startup"""
        try:
            # Try registry method first
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                0, winreg.KEY_WRITE
            )
            
            winreg.SetValueEx(reg_key, APP_NAME, 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(reg_key)
            return True
        except:
            # Fallback to startup folder method
            try:
                startup_folder = self.get_startup_folder()
                shortcut_path = os.path.join(startup_folder, f"{{APP_NAME}}.lnk")
                
                # Create shortcut using PowerShell
                ps_script = f'''
                $WshShell = New-Object -ComObject WScript.Shell
                $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
                $Shortcut.TargetPath = "{app_path}"
                $Shortcut.Save()
                '''
                
                # Execute PowerShell script
                subprocess.run(["powershell", "-Command", ps_script], check=True)
                return True
            except:
                return False
    
    def remove_from_startup(self):
        """Remove app from Windows startup"""
        try:
            # Try registry method first
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                0, winreg.KEY_WRITE
            )
            
            try:
                winreg.DeleteValue(reg_key, APP_NAME)
            except WindowsError:
                pass
            finally:
                winreg.CloseKey(reg_key)
        except:
            # Fallback to startup folder method
            try:
                startup_folder = self.get_startup_folder()
                shortcut_path = os.path.join(startup_folder, f"{{APP_NAME}}.lnk")
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
            except:
                pass
    
    def get_startup_folder(self):
        """Get the Windows startup folder path"""
        try:
            # Try to get startup folder from registry
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                              r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders") as key:
                startup_folder = winreg.QueryValueEx(key, "Startup")[0]
                return startup_folder
        except:
            # Fallback to standard location
            return os.path.join(os.environ['APPDATA'], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            f"{{APP_NAME}} v{{APP_VERSION}}\\n\\n"
            f"This application connects to the AMRS Preventative Maintenance System.\\n"
            f"Server URL: {{SERVER_URL}}"
        )

def is_admin():
    """Check if the script is running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    """Re-run the script with admin privileges"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        script = sys.executable
    else:
        # Running as script
        script = sys.argv[0]
        
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script, None, 1)

if __name__ == "__main__":
    # Try to enable DPI awareness
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # Check if admin rights are needed for startup feature
    if len(sys.argv) > 1 and sys.argv[1] == "--configure-startup" and not is_admin():
        run_as_admin()
        sys.exit(0)
    
    # Create and run standalone window
    app = StandaloneWindow()
    app.mainloop()
""")
print(f"Created {MAIN_SCRIPT}")

# Create batch file for fallback option
print(f"Creating batch launcher: {BATCH_FILE}")
with open(BATCH_FILE, "w") as f:
    f.write(f"""@echo off
echo Starting {APP_NAME} v{APP_VERSION}...
echo.

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Check if the script exists
if not exist "{MAIN_SCRIPT}" (
    echo ERROR: Could not find {MAIN_SCRIPT}
    echo Please make sure the script is in the same folder as this batch file.
    echo.
    pause
    exit /b 1
)

REM Install required packages if missing
pip install tkinter --quiet
pip install pywin32 --quiet

REM Run the application
echo Connecting to {SERVER_URL}...
python "{MAIN_SCRIPT}"

REM If we got here, Python script has exited
echo.
echo Application closed.
if %errorlevel% neq 0 (
    echo There was an error running the application.
    pause
)
""")

print(f"Created batch launcher in {BATCH_FILE}")

# Copy main script to dist folder
shutil.copy(MAIN_SCRIPT, os.path.join(OUTPUT_DIR, MAIN_SCRIPT))
print(f"Copied {MAIN_SCRIPT} to {OUTPUT_DIR}/")

# Try to build with PyInstaller
try:
    print("Attempting to build executable with PyInstaller...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"Using PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not installed. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("PyInstaller installed successfully.")
        except subprocess.SubprocessError:
            print("Could not install PyInstaller. Falling back to batch file launcher.")
            print(f"You can run the application using: {BATCH_FILE}")
            sys.exit(0)
    
    # Create a spec file for PyInstaller with additional dependencies
    spec_file = "amrs_app.spec"
    with open(spec_file, "w", encoding="utf-8") as f:
        f.write(f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['winreg'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
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
    icon='amrs_icon.ico' if os.path.exists('amrs_icon.ico') else None,
)
""")
    
    # Try to install additional dependencies if needed
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
    except:
        print("Warning: Failed to install pywin32. Continuing anyway...")
    
    # Build with PyInstaller using the spec file
    print("Building executable...")
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        spec_file
    ]
    
    result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\n[SUCCESS] PyInstaller build successful!")
        exe_path = os.path.join("dist", f"{APP_NAME.replace(' ', '')}.exe")
        if os.path.exists(exe_path):
            print(f"\nExecutable created: {os.path.abspath(exe_path)}")
        else:
            print(f"\nWarning: Expected executable not found at {exe_path}")
            print("Falling back to batch file launcher.")
    else:
        print("PyInstaller build failed with errors:")
        print(result.stderr)
        print("\nFalling back to batch file launcher.")
        print(f"You can run the application using: {BATCH_FILE}")

except Exception as e:
    print(f"\n[ERROR] Error during build: {str(e)}")
    print("\nFalling back to batch file launcher.")
    print(f"You can run the application using: {BATCH_FILE}")

print("\n" + "=" * 60)
print(f"Build process complete for {APP_NAME} v{APP_VERSION}")
print(f"The application will connect to: {SERVER_URL}")
print("\nTo run the application:")
print(f"1. Navigate to the '{OUTPUT_DIR}' folder")
print(f"2. Run the '{APP_NAME.replace(' ', '')}.exe' file or 'AMRS_Launcher.bat' if EXE was not created")
print("=" * 60)