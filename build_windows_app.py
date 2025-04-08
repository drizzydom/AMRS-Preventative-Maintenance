"""
Build script for creating a Windows executable that automatically connects
to the AMRS Preventative Maintenance application deployed on Render.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
import base64
import platform

# Configuration
APP_NAME = "AMRS Maintenance Tracker"
APP_VERSION = "1.0.0"
APP_ICON = "icon.ico"
SERVER_URL = "https://amrs-preventative-maintenance.onrender.com"
MAIN_PY = "windows_app.py"
OUTPUT_DIR = "dist"
BUILD_DIR = "build"

# Check for prerequisites
def check_prerequisites():
    """Check that all prerequisites are met before attempting build"""
    
    # Check Python version - NumPy has issues with Python 3.11+ on Windows
    print(f"Checking Python version...")
    python_version = platform.python_version_tuple()
    if int(python_version[0]) >= 3 and int(python_version[1]) >= 11:
        print(f"⚠️ WARNING: You're using Python {platform.python_version()}")
        print(f"   NumPy and other dependencies may have issues with Python 3.11+")
        print(f"   Consider using Python 3.8-3.10 for building the application")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Build aborted.")
            sys.exit(1)
    else:
        print(f"✓ Python {platform.python_version()} is compatible")
    
    # Check for Microsoft Visual C++ Build Tools
    print("Checking for Microsoft Visual C++ Build Tools...")
    try:
        # Try to compile a simple C program to test if MSVC is available
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.c', delete=False) as f:
            f.write(b'int main() { return 0; }')
            test_file = f.name
        
        # Try to compile with MSVC
        try:
            subprocess.run(['cl', test_file], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=True)
            os.remove(test_file)
            print("✓ Microsoft Visual C++ Build Tools found")
        except (subprocess.SubprocessError, FileNotFoundError):
            print("❌ Microsoft Visual C++ Build Tools not found or not in PATH")
            print("\nTo install Visual C++ Build Tools:")
            print("1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
            print("2. During installation, select 'Desktop development with C++'")
            print("3. Restart your computer after installation")
            print("\nAlternatively, use the pre-built release from:")
            print("https://github.com/yourusername/AMRS-Preventative-Maintenance/releases")
            sys.exit(1)
            
    except Exception as e:
        print(f"⚠️ Could not verify build tools: {str(e)}")
        print("Continuing but build may fail if tools are missing.")
    
    # Check for PyInstaller
    print("Checking for PyInstaller...")
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} is installed")
    except ImportError:
        print("❌ PyInstaller not found")
        print("Installing PyInstaller...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✓ PyInstaller installed successfully")
        except subprocess.SubprocessError:
            print("❌ Failed to install PyInstaller")
            sys.exit(1)

# Call the prerequisites check before proceeding
check_prerequisites()

# Ensure required directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BUILD_DIR, exist_ok=True)

# Create the main launcher file
print(f"Creating main application file: {MAIN_PY}")
with open(MAIN_PY, 'w') as f:
    f.write(f'''
import sys
import webbrowser
import os
import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
import shutil
from pathlib import Path
import subprocess
import urllib.request
import urllib.error

# Configuration
SERVER_URL = "{SERVER_URL}"
APP_NAME = "{APP_NAME}"
APP_VERSION = "{APP_VERSION}"
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.amrs-maintenance')

# Create config directory if it doesn't exist
os.makedirs(CONFIG_DIR, exist_ok=True)
config_file = os.path.join(CONFIG_DIR, 'config.json')
login_file = os.path.join(CONFIG_DIR, 'login.json')

# Default configurations
default_config = {{
    'server_url': SERVER_URL,
    'auto_connect': True,
    'check_updates': True,
    'launch_browser': True
}}

class AMRSMaintenanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("600x400")
        self.root.minsize(500, 300)
        
        # Set app icon if available
        try:
            icon_path = os.path.join(os.path.dirname(sys.executable), "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # Ignore icon errors
            
        # Load configuration
        self.config = self.load_config()
        
        # Create the UI
        self.create_ui()
        
        # Check server connectivity
        self.check_server_thread = threading.Thread(target=self.check_server_connection)
        self.check_server_thread.daemon = True
        self.check_server_thread.start()
        
    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return default_config.copy()
        else:
            # Save default config
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config.copy()
            
    def save_config(self):
        """Save current configuration to file"""
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def create_ui(self):
        """Create the main user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # App title and version
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text=APP_NAME, font=("", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        version_label = ttk.Label(title_frame, text=f"v{APP_VERSION}", font=("", 10))
        version_label.pack(side=tk.LEFT, padx=(5, 0), pady=(5, 0))
        
        # Server status
        self.status_frame = ttk.LabelFrame(main_frame, text="Server Status")
        self.status_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.status_text = tk.StringVar(value="Checking server status...")
        status_label = ttk.Label(self.status_frame, textvariable=self.status_text)
        status_label.pack(pady=10, padx=10)
        
        # Server URL
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 15))
        
        url_label = ttk.Label(url_frame, text="Server URL:")
        url_label.pack(side=tk.LEFT)
        
        self.url_var = tk.StringVar(value=self.config['server_url'])
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=40)
        url_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Action buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 20))
        
        connect_btn = ttk.Button(btn_frame, text="Connect to Server", command=self.open_browser)
        connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        settings_btn = ttk.Button(btn_frame, text="Settings", command=self.open_settings)
        settings_btn.pack(side=tk.LEFT)
        
        quit_btn = ttk.Button(btn_frame, text="Quit", command=self.root.quit)
        quit_btn.pack(side=tk.RIGHT)
        
        # Auto-connect checkbox
        self.auto_connect_var = tk.BooleanVar(value=self.config['auto_connect'])
        auto_connect_cb = ttk.Checkbutton(main_frame, text="Automatically connect on startup", 
                                         variable=self.auto_connect_var,
                                         command=self.toggle_auto_connect)
        auto_connect_cb.pack(anchor=tk.W)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Auto-connect if enabled
        if self.config['auto_connect']:
            self.root.after(1500, self.open_browser)
            
    def toggle_auto_connect(self):
        """Toggle auto-connect setting"""
        self.config['auto_connect'] = self.auto_connect_var.get()
        self.save_config()
            
    def check_server_connection(self):
        """Check if the server is available"""
        try:
            # Try to connect to the server
            server_url = self.config['server_url']
            with urllib.request.urlopen(f"{{server_url}}/health") as response:
                if response.status == 200:
                    self.update_status("Connected", "green")
                    return True
                else:
                    self.update_status(f"Server error: {{response.status}}", "red")
        except urllib.error.URLError:
            self.update_status("Cannot reach server", "red")
        except Exception as e:
            self.update_status(f"Error: {{str(e)}}", "red")
        return False
            
    def update_status(self, message, color="black"):
        """Update the status message"""
        def _update():
            self.status_text.set(message)
            # Use tag to set color if Label supports it, otherwise leave as is
            try:
                self.status_label.config(foreground=color)
            except:
                pass
            self.status_bar.config(text=f"Status: {{message}}")
        
        # Schedule update on main thread
        self.root.after(0, _update)
            
    def open_browser(self):
        """Open the server URL in the default web browser"""
        server_url = self.url_var.get().strip()
        if not server_url:
            server_url = SERVER_URL
            
        self.config['server_url'] = server_url
        self.save_config()
        
        try:
            self.update_status(f"Opening {{server_url}}...")
            webbrowser.open(server_url)
            self.update_status("Browser opened", "green")
        except Exception as e:
            self.update_status(f"Error opening browser: {{str(e)}}", "red")
            messagebox.showerror("Error", f"Could not open browser: {{str(e)}}")
            
    def open_settings(self):
        """Open settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Create settings UI
        settings_frame = ttk.Frame(settings_window, padding="20")
        settings_frame.pack(expand=True, fill=tk.BOTH)
        
        # Server URL
        url_frame = ttk.Frame(settings_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        url_label = ttk.Label(url_frame, text="Server URL:")
        url_label.pack(side=tk.LEFT)
        
        url_var = tk.StringVar(value=self.config['server_url'])
        url_entry = ttk.Entry(url_frame, textvariable=url_var, width=35)
        url_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Auto connect option
        auto_connect_var = tk.BooleanVar(value=self.config['auto_connect'])
        auto_connect_cb = ttk.Checkbutton(settings_frame, text="Automatically connect on startup", 
                                         variable=auto_connect_var)
        auto_connect_cb.pack(anchor=tk.W, pady=(0, 5))
        
        # Check for updates option
        check_updates_var = tk.BooleanVar(value=self.config.get('check_updates', True))
        check_updates_cb = ttk.Checkbutton(settings_frame, text="Check for updates on startup", 
                                         variable=check_updates_var)
        check_updates_cb.pack(anchor=tk.W, pady=(0, 5))
        
        # Reset to default button
        def reset_defaults():
            url_var.set(SERVER_URL)
            auto_connect_var.set(True)
            check_updates_var.set(True)
            
        reset_btn = ttk.Button(settings_frame, text="Reset to Defaults", command=reset_defaults)
        reset_btn.pack(anchor=tk.W, pady=(10, 0))
        
        # Save button
        def save_settings():
            self.config['server_url'] = url_var.get().strip()
            self.config['auto_connect'] = auto_connect_var.get()
            self.config['check_updates'] = check_updates_var.get()
            self.save_config()
            self.url_var.set(self.config['server_url'])
            self.auto_connect_var.set(self.config['auto_connect'])
            settings_window.destroy()
            
        save_btn = ttk.Button(settings_window, text="Save", command=save_settings)
        save_btn.pack(side=tk.RIGHT, padx=20, pady=20)
        
        # Cancel button
        cancel_btn = ttk.Button(settings_window, text="Cancel", command=settings_window.destroy)
        cancel_btn.pack(side=tk.RIGHT, pady=20)
        
        # Center the window
        settings_window.update_idletasks()
        width = settings_window.winfo_width()
        height = settings_window.winfo_height()
        x = (settings_window.winfo_screenwidth() // 2) - (width // 2)
        y = (settings_window.winfo_screenheight() // 2) - (height // 2)
        settings_window.geometry(f"{{width}}x{{height}}+{{x}}+{{y}}")
        
if __name__ == "__main__":
    # Enable DPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # Create and run the app
    root = tk.Tk()
    app = AMRSMaintenanceApp(root)
    root.mainloop()
''')
print(f"Created {MAIN_PY}")

# Check if icon file exists, create if not
if not os.path.exists(APP_ICON):
    print(f"Creating icon file: {APP_ICON}")
    try:
        # Create a simple orange square icon as placeholder
        from PIL import Image, ImageDraw
        
        img = Image.new('RGB', (256, 256), color=(254, 121, 0))  # AMRS orange
        d = ImageDraw.Draw(img)
        
        # Add a simple gear shape
        d.ellipse((48, 48, 208, 208), fill=(220, 100, 0))
        d.ellipse((80, 80, 176, 176), fill=(254, 121, 0))
        
        # Save as icon
        img.save(APP_ICON)
        print(f"Created placeholder icon: {APP_ICON}")
    except Exception as e:
        print(f"Error creating icon: {str(e)}")
        print("Continuing without icon...")

# Run PyInstaller
print("\nBuilding Windows application with PyInstaller...")
pyinstaller_cmd = [
    'pyinstaller',
    '--name', APP_NAME.replace(' ', ''),
    '--onefile',
    '--windowed',
    f'--icon={APP_ICON}',
    '--add-data', f'{APP_ICON};.',
    '--clean',
    MAIN_PY
]

try:
    subprocess.run(pyinstaller_cmd, check=True)
    print("\n✅ Build completed successfully!")
    
    # Get the executable path
    exe_path = os.path.join('dist', f"{APP_NAME.replace(' ', '')}.exe")
    if os.path.exists(exe_path):
        print(f"\nExecutable created at: {os.path.abspath(exe_path)}")
        print(f"\nThe application will automatically connect to: {SERVER_URL}")
    else:
        print("\n⚠️ Executable not found where expected. Check the 'dist' directory.")
    
except Exception as e:
    print(f"\n❌ Build failed: {str(e)}")
    print("\nTroubleshooting tips:")
    print("1. Make sure PyInstaller is installed: pip install pyinstaller")
    print("2. Try running in a clean virtual environment")
    print("3. Check for any dependencies that might be missing")
    sys.exit(1)

print("\nDone! You can distribute the executable from the 'dist' directory.")
