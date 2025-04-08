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
with open(MAIN_SCRIPT, "w", encoding="utf-8") as f:  # Added UTF-8 encoding
    f.write("""
import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.error
import threading
import time

# Configuration
SERVER_URL = "{0}"
APP_NAME = "{1}"
APP_VERSION = "{2}"

class SimpleApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("500x350")
        self.root.minsize(500, 350)
        
        # Main frame with some padding
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # App header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(
            header_frame, 
            text=APP_NAME,
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # Server URL input
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 15))
        
        url_label = ttk.Label(url_frame, text="Server URL:")
        url_label.pack(side=tk.LEFT)
        
        self.url_var = tk.StringVar(value=SERVER_URL)
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        url_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # Server status section
        status_frame = ttk.LabelFrame(main_frame, text="Server Status")
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.status_var = tk.StringVar(value="Checking connection...")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, padding=10)
        self.status_label.pack(fill=tk.X)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.connect_btn = ttk.Button(
            button_frame, 
            text="Connect to AMRS Maintenance System", 
            command=self.open_browser
        )
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_btn = ttk.Button(
            button_frame, 
            text="Check Connection", 
            command=self.check_connection
        )
        self.refresh_btn.pack(side=tk.LEFT)
        
        quit_btn = ttk.Button(button_frame, text="Exit", command=self.root.quit)
        quit_btn.pack(side=tk.RIGHT)
        
        # Auto connect checkbox
        self.auto_connect_var = tk.BooleanVar(value=True)
        auto_connect_cb = ttk.Checkbutton(
            main_frame, 
            text="Automatically connect on startup", 
            variable=self.auto_connect_var
        )
        auto_connect_cb.pack(anchor=tk.W, pady=(0, 10))
        
        # Version info
        version_label = ttk.Label(
            main_frame, 
            text=f"Version {{APP_VERSION}}",
            foreground="gray"
        )
        version_label.pack(side=tk.BOTTOM, anchor=tk.SE, pady=(20, 0))
        
        # Start connection check in a separate thread
        threading.Thread(target=self.check_connection, daemon=True).start()
        
        # Auto-connect if enabled (after a short delay)
        if self.auto_connect_var.get():
            self.root.after(1500, self.open_browser)
            
    def check_connection(self):
        self.status_var.set("Checking server connection...")
        self.status_label.configure(foreground="black")
        self.root.update()
        
        try:
            # Disable connect button during check
            self.connect_btn.configure(state="disabled")
            self.refresh_btn.configure(state="disabled")
            
            # Try to connect to the server
            url = self.url_var.get().strip()
            start_time = time.time()
            
            try:
                with urllib.request.urlopen(f"{{url}}/health", timeout=5) as response:
                    elapsed = time.time() - start_time
                    if response.status == 200:
                        self.status_var.set(f"[OK] Server is online! ({{elapsed:.2f}}s)")
                        self.status_label.configure(foreground="green")
                    else:
                        self.status_var.set(f"[WARNING] Server responded with status: {{response.status}}")
                        self.status_label.configure(foreground="orange")
            except urllib.error.URLError as e:
                self.status_var.set(f"[ERROR] Cannot connect to server")
                self.status_label.configure(foreground="red")
            except Exception as e:
                self.status_var.set(f"[ERROR] {{str(e)}}")
                self.status_label.configure(foreground="red")
        finally:
            # Re-enable buttons
            self.connect_btn.configure(state="normal")
            self.refresh_btn.configure(state="normal")
    
    def open_browser(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid server URL")
            return
            
        try:
            webbrowser.open(url)
            self.status_var.set(f"Opened {{url}} in your browser")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not open browser: {{str(e)}}")
            self.status_var.set(f"Error: {{str(e)}}")

if __name__ == "__main__":
    # Create and run the application
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()
""".format(SERVER_URL, APP_NAME, APP_VERSION))

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
    
    # Build with PyInstaller
    print("Building executable...")
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME.replace(" ", ""),
        "--onefile",
        "--windowed",
        MAIN_SCRIPT
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
print(f"2. Run 'AMRSMaintenanceTracker.exe' or '{os.path.basename(BATCH_FILE)}' if EXE wasn't created")
print("=" * 60)