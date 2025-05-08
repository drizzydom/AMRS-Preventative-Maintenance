import os
import sys
import subprocess
import threading
import time
import logging
import signal
import webview
import winreg
import ctypes
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[WIN_APP] %(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("win_app")

# Get the application directory
if getattr(sys, 'frozen', False):
    # Running as a bundled executable
    APP_DIR = os.path.dirname(sys.executable)
else:
    # Running as a script
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the bootstrap script and flask app
BOOTSTRAP_SCRIPT = os.path.join(APP_DIR, 'app_bootstrap.py')
FLASK_PORT = 10000
FLASK_URL = f"http://localhost:{FLASK_PORT}"

# Global variables
flask_process = None
window = None
app_running = True

def is_webview2_installed():
    """Check if WebView2 Runtime is installed"""
    try:
        # Try to open the WebView2 registry key
        key_path = r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
        winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        logger.info("WebView2 Runtime is installed")
        return True
    except WindowsError:
        try:
            # Check 32-bit registry on 64-bit Windows
            key_path = r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
            winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            logger.info("WebView2 Runtime is installed")
            return True
        except WindowsError:
            logger.warning("WebView2 Runtime is not installed")
            return False

def download_webview2():
    """Download and install WebView2 Runtime"""
    logger.info("Downloading WebView2 Runtime installer...")
    import urllib.request
    import tempfile
    
    # URL for the WebView2 Evergreen Bootstrapper
    url = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
    installer_path = os.path.join(tempfile.gettempdir(), "MicrosoftEdgeWebview2Setup.exe")
    
    try:
        # Download the installer
        urllib.request.urlretrieve(url, installer_path)
        logger.info(f"WebView2 installer downloaded to {installer_path}")
        
        # Run the installer
        logger.info("Installing WebView2 Runtime...")
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", installer_path, "/silent /install", None, 1
        )
        
        if result > 32:
            logger.info("WebView2 installation started successfully")
            # Wait for installation to complete (approximate)
            time.sleep(30)
            return True
        else:
            logger.error(f"Failed to start WebView2 installation. Error code: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Error downloading or installing WebView2: {e}")
        return False

def start_flask():
    """Start the Flask application using the bootstrap script"""
    global flask_process
    
    logger.info(f"Starting Flask application from {BOOTSTRAP_SCRIPT}")
    
    try:
        # Start the Flask app using the bootstrap script
        flask_process = subprocess.Popen(
            [sys.executable, BOOTSTRAP_SCRIPT, '--port', str(FLASK_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW  # Hide console window
        )
        
        # Start threads to read stdout and stderr
        threading.Thread(target=read_output, args=(flask_process.stdout, "FLASK_OUT"), daemon=True).start()
        threading.Thread(target=read_output, args=(flask_process.stderr, "FLASK_ERR"), daemon=True).start()
        
        # Wait for Flask to start up
        logger.info(f"Waiting for Flask to start at {FLASK_URL}")
        for _ in range(30):  # Try for 30 seconds
            try:
                import urllib.request
                with urllib.request.urlopen(FLASK_URL, timeout=1) as response:
                    if response.status == 200:
                        logger.info("Flask server is running")
                        return True
            except Exception:
                pass
            time.sleep(1)
        
        logger.error("Failed to start Flask server")
        return False
        
    except Exception as e:
        logger.error(f"Error starting Flask: {e}")
        return False

def read_output(pipe, prefix):
    """Read output from a pipe and log it"""
    try:
        for line in iter(pipe.readline, ''):
            if line:
                logger.info(f"[{prefix}] {line.strip()}")
    except Exception as e:
        logger.error(f"Error reading {prefix}: {e}")

def create_window():
    """Create the webview window"""
    global window
    
    # Define window closing handler
    def on_closing():
        global app_running
        logger.info("Window closing, shutting down application...")
        app_running = False
        if flask_process:
            try:
                logger.info("Terminating Flask process...")
                flask_process.terminate()
                flask_process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error terminating Flask: {e}")
                try:
                    flask_process.kill()
                except:
                    pass
    
    # Create the window
    logger.info("Creating application window...")
    window = webview.create_window(
        'AMRS Maintenance Tracker', 
        FLASK_URL,
        width=1200,
        height=800,
        min_size=(800, 600),
        background_color='#FFFFFF'
    )
    window.closing += on_closing
    
    # Start webview
    logger.info("Starting webview...")
    webview.start(debug=False)

def main():
    """Main application entry point"""
    logger.info("Starting AMRS Maintenance Tracker")
    
    # Check if WebView2 is installed, if not try to install it
    if not is_webview2_installed():
        logger.warning("WebView2 Runtime not detected")
        result = download_webview2()
        if not result:
            logger.error("Failed to install WebView2 Runtime")
            ctypes.windll.user32.MessageBoxW(
                0,
                "Microsoft Edge WebView2 Runtime is required but could not be installed automatically.\n"
                "Please download and install it from:\n"
                "https://developer.microsoft.com/en-us/microsoft-edge/webview2/",
                "WebView2 Runtime Required",
                0x10  # MB_ICONERROR
            )
            return
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    flask_thread.join(timeout=10)  # Wait max 10 seconds for Flask to start
    
    # Check if Flask started successfully
    if not flask_process or flask_process.poll() is not None:
        logger.error("Flask process failed to start or crashed immediately")
        ctypes.windll.user32.MessageBoxW(
            0,
            "Failed to start the Flask application.\n"
            "Please check the logs for more information.",
            "Application Error",
            0x10  # MB_ICONERROR
        )
        return
    
    # Create and start the window
    create_window()
    
    # Wait for window to close
    while app_running:
        time.sleep(0.1)
    
    logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()