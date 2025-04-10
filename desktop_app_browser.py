"""
AMRS Maintenance Tracker - Browser Version
Simplified desktop app that uses the system browser without CEF
"""
import os
import sys
import time
import logging
import subprocess
import webbrowser
import socket
import signal
import platform
from pathlib import Path

# Configuration
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
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port():
    """Find an available port to use"""
    start_port = 8000
    max_port = 9000
    for port in range(start_port, max_port):
        if not is_port_in_use(port):
            return port
    return start_port  # Default if all ports are in use

def locate_app_py():
    """Find the Flask app script"""
    # Define possible locations relative to this script
    possible_locations = [
        "app.py",
        os.path.join("..", "app.py"),
        os.path.join("app", "app.py"),
    ]
    
    for location in possible_locations:
        abs_path = os.path.abspath(location)
        if os.path.exists(abs_path):
            logger.info(f"Found app.py at {abs_path}")
            return abs_path
    
    # If not found, use the first location as a guess
    default_location = os.path.abspath("app.py")
    logger.warning(f"app.py not found, using default: {default_location}")
    return default_location

def start_flask():
    """Start the Flask server process"""
    app_script = locate_app_py()
    port = find_available_port()
    
    logger.info(f"Starting Flask server on port {port}")
    
    # Prepare command to run Flask app
    cmd = [sys.executable, app_script, "--port", str(port)]
    
    try:
        # Start Flask in a new process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        
        # Check that process started correctly
        if process.poll() is not None:
            logger.error(f"Flask process failed to start - exit code: {process.returncode}")
            return None, None
        
        return process, port
    
    except Exception as e:
        logger.error(f"Error starting Flask: {str(e)}")
        return None, None

def wait_for_flask_server(port, timeout=30):
    """Wait for the Flask server to become available"""
    logger.info(f"Waiting for Flask server on port {port}")
    start_time = time.time()
    
    while (time.time() - start_time) < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex(('localhost', port)) == 0:
                    logger.info(f"Flask server is ready on port {port}")
                    return True
        except:
            pass
            
        time.sleep(0.5)
    
    logger.error(f"Timed out waiting for Flask server on port {port}")
    return False

def open_browser(url):
    """Open URL in the default web browser"""
    logger.info(f"Opening {url} in default browser")
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        logger.error(f"Error opening browser: {str(e)}")
        return False

def main():
    """Main function to run the application"""
    try:
        print(f"Starting {APP_NAME} v{APP_VERSION}")
        print(f"Logs: {LOG_PATH}")
        
        # Start Flask server
        flask_process, port = start_flask()
        if not flask_process or not port:
            print("Failed to start application server")
            input("Press Enter to exit...")
            return 1
        
        # Wait for Flask to start
        url = f"http://localhost:{port}"
        if not wait_for_flask_server(port):
            print("Timed out waiting for application server")
            if flask_process:
                flask_process.terminate()
            input("Press Enter to exit...")
            return 1
            
        # Open in browser
        if not open_browser(url):
            print(f"Failed to open browser automatically. Please open {url} manually.")
        
        print("\n" + "=" * 60)
        print(f"  {APP_NAME} is running at: {url}")
        print("=" * 60)
        print("\nThe application is running in your default browser.")
        print("Close this window to shut down the application when you're done.")
        
        # Keep running until user terminates
        try:
            while True:
                # Check if Flask is still running
                if flask_process.poll() is not None:
                    logger.error("Flask server stopped unexpectedly")
                    print("Application server has stopped unexpectedly")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        # Terminate Flask
        print("\nShutting down application...")
        if flask_process:
            if platform.system() == "Windows":
                # On Windows, terminate process tree
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(flask_process.pid)], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # On Unix systems
                flask_process.terminate()
                try:
                    flask_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    flask_process.kill()
        
        print("Application shut down successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
