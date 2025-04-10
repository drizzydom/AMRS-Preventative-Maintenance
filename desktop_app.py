"""
AMRS Maintenance Tracker - Desktop Application
Uses CEF Python to display the web UI in a desktop application
"""
import os
import sys
import time
import logging
import subprocess
import socket
import platform
import signal
import webbrowser
from pathlib import Path

# Set up base directory - handle both script and frozen executable
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure application paths
APP_NAME = "AMRS Maintenance Tracker"
APP_VERSION = "1.0.0"
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".amrs-maintenance")
LOG_PATH = os.path.join(APP_DATA_DIR, "desktop_app.log")
BROWSER_MODE = False  # Set to True to use system browser instead of CEF

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

# Try to import CEF Python - fallback to browser mode if it fails
try:
    logger.info("Attempting to import cefpython3...")
    from cefpython3 import cefpython as cef
    logger.info("Successfully imported cefpython3")
    BROWSER_MODE = False
except ImportError as e:
    logger.warning(f"Failed to import cefpython3: {e}")
    logger.warning("Falling back to system browser mode")
    BROWSER_MODE = True
except Exception as e:
    logger.error(f"Unexpected error importing cefpython3: {e}")
    logger.warning("Falling back to system browser mode")
    BROWSER_MODE = True

def get_available_port():
    """Find an available port to run the Flask server on"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def find_app_py():
    """Find the app.py file in various locations"""
    possible_locations = [
        os.path.join(BASE_DIR, "app.py"),
        os.path.join(os.path.dirname(BASE_DIR), "app.py"),
        os.path.abspath("app.py"),
        # For development environment
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"),
    ]
    
    for location in possible_locations:
        if os.path.exists(location):
            logger.info(f"Found app.py at {location}")
            return location
            
    # If not found, create a temporary app.py file with essential functionality
    logger.warning("app.py not found in any location. Creating temporary Flask app.")
    temp_app_path = os.path.join(BASE_DIR, "temp_app.py")
    
    with open(temp_app_path, "w") as f:
        f.write("""
from flask import Flask, jsonify

# Create Flask application
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'Flask server running', 
        'message': 'This is a temporary app. The main app could not be found.'
    })

# Add a test route
@app.route('/test')
def test():
    return jsonify({
        'status': 'success',
        'message': 'Test endpoint working'
    })

if __name__ == '__main__':
    import sys
    port = 5000
    # Check for --port argument
    if len(sys.argv) > 2 and sys.argv[1] == "--port":
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Invalid port: {sys.argv[2]}, using default: 5000")
    # Run the Flask app
    app.run(host='127.0.0.1', port=port, debug=False)
""")
    
    logger.info(f"Created temporary app at {temp_app_path}")
    return temp_app_path

def start_flask_server(port):
    """Start the Flask server in a separate process"""
    try:
        app_script = find_app_py()
        
        logger.info(f"Starting Flask server on port {port}")
        
        # In PyInstaller context we need to run the script differently
        if getattr(sys, 'frozen', False):
            # Running as executable - we need to run as a module
            # Create a wrapper script that we can execute
            wrapper_script = os.path.join(BASE_DIR, "run_flask.py")
            with open(wrapper_script, "w") as f:
                f.write(f"""
import os
import sys
import importlib.util

# Load the Flask app from the app.py file
spec = importlib.util.spec_from_file_location("app", r"{app_script}")
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

# Setup and run the Flask app
if hasattr(app_module, 'app'):
    flask_app = app_module.app
    flask_app.run(port={port}, debug=False)
else:
    print("Error: Flask app not found in the module")
    sys.exit(1)
""")

            # Run the wrapper script
            cmd = [sys.executable, wrapper_script]
            logger.info(f"Starting Flask with command: {' '.join(cmd)}")
        else:
            # Development mode - run app.py directly
            cmd = [
                sys.executable, 
                app_script,
                "--port", str(port)
            ]
            logger.info(f"Starting Flask with command: {' '.join(cmd)}")
        
        # Start Flask in a new process
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check if process started successfully
        if process.poll() is not None:
            logger.error(f"Flask process failed to start: Exit code {process.returncode}")
            stderr = process.stderr.read() if process.stderr else "No error output available"
            logger.error(f"Error: {stderr}")
            return None
            
        logger.info(f"Flask server started on port {port}")
        return process
            
    except Exception as e:
        logger.error(f"Error starting Flask server: {e}", exc_info=True)
        return None

def wait_for_flask_server(port, timeout=10):
    """Wait for Flask server to become available"""
    start_time = time.time()
    logger.info(f"Waiting for Flask server on port {port}...")
    
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:  # Port is open and accepting connections
                logger.info(f"Flask server is ready on port {port}")
                return True
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)
    
    logger.error(f"Timed out waiting for Flask server on port {port}")
    return False

def setup_cef():
    """Set up CEF browser"""
    if BROWSER_MODE:
        return True
        
    try:
        logger.info("Initializing CEF...")
        sys.excepthook = cef.ExceptHook  # To shutdown CEF processes on exception
        
        # CEF configuration settings
        settings = {
            "product_version": APP_NAME + "/" + APP_VERSION,
            "user_agent": f"{APP_NAME}/{APP_VERSION} CEF Python/{cef.__version__}",
            "cache_path": os.path.join(APP_DATA_DIR, "cef_cache"),
            "log_severity": cef.LOGSEVERITY_INFO,
            "log_file": os.path.join(APP_DATA_DIR, "cef_debug.log"),
            "release_dcheck_enabled": False,  # Remove this setting for production
            "browser_subprocess_path": "%s/%s" % (
                cef.GetModuleDirectory(), "subprocess"),
        }
        
        # Initialize CEF
        cef.Initialize(settings=settings)
        logger.info("CEF initialized")
        return True
    except Exception as e:
        logger.error(f"Error initializing CEF: {e}")
        return False

def create_browser_window(url):
    """Create and configure the CEF browser window"""
    if BROWSER_MODE:
        return None
        
    try:
        logger.info(f"Creating CEF browser window for {url}")
        window_info = cef.WindowInfo()
        window_info.SetAsChild(0, [0, 0, 1200, 800])  # Initial size
        
        # Create browser
        browser = cef.CreateBrowserSync(
            window_info=window_info,
            url=url
        )
        
        logger.info("Browser window created")
        return browser
    except Exception as e:
        logger.error(f"Error creating browser window: {e}")
        return None

def browser_mode_open(url):
    """Open the URL in the system's default browser"""
    logger.info(f"Opening {url} in system browser...")
    webbrowser.open(url)

def handle_shutdown(flask_process):
    """Clean shutdown procedure"""
    logger.info("Performing cleanup before exit...")
    
    # Terminate Flask server
    if flask_process:
        try:
            logger.info("Terminating Flask server...")
            # On Windows we need to kill the process tree
            if platform.system() == "Windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(flask_process.pid)])
            else:
                flask_process.terminate()
                flask_process.wait(timeout=3)
        except Exception as e:
            logger.error(f"Error terminating Flask server: {e}")
    
    # Shutdown CEF if used
    if not BROWSER_MODE:
        try:
            logger.info("Shutting down CEF...")
            cef.Shutdown()
        except Exception as e:
            logger.error(f"Error shutting down CEF: {e}")

def main():
    """Main function to run the desktop application"""
    try:
        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Operating system: {platform.system()} {platform.release()}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Base directory: {BASE_DIR}")
        logger.info(f"Browser mode: {'Enabled' if BROWSER_MODE else 'Disabled'}")
        
        # Get an available port for the Flask server
        port = get_available_port()
        
        # Start Flask server
        flask_process = start_flask_server(port)
        if not flask_process:
            logger.error("Failed to start Flask server. Exiting.")
            return 1
        
        # Wait for Flask server to start
        if not wait_for_flask_server(port):
            logger.error("Flask server did not start in time. Exiting.")
            if flask_process:
                flask_process.terminate()
            return 1
        
        # Define URL
        url = f"http://localhost:{port}"
        
        if BROWSER_MODE:
            # Open in default browser
            browser_mode_open(url)
            print(f"\n{APP_NAME} has been opened in your default browser")
            print("Close this window to exit the application")
            
            # Keep app running
            try:
                while True:
                    if flask_process.poll() is not None:
                        logger.error("Flask server unexpectedly terminated")
                        return 1
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
            finally:
                handle_shutdown(flask_process)
        else:
            # Use CEF browser
            if not setup_cef():
                logger.error("Failed to initialize CEF. Falling back to browser mode.")
                browser_mode_open(url)
                
                # Keep app running 
                try:
                    while True:
                        if flask_process.poll() is not None:
                            logger.error("Flask server unexpectedly terminated")
                            return 1
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Received keyboard interrupt, shutting down...")
                finally:
                    handle_shutdown(flask_process)
                return 0
            
            # Create browser window
            browser = create_browser_window(url)
            if not browser:
                logger.error("Failed to create browser window. Falling back to browser mode.")
                browser_mode_open(url)
                
                # Keep app running 
                try:
                    while True:
                        if flask_process.poll() is not None:
                            logger.error("Flask server unexpectedly terminated")
                            return 1
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Received keyboard interrupt, shutting down...")
                finally:
                    handle_shutdown(flask_process)
                return 0
            
            # Set up handler for application exit
            def exit_handler():
                handle_shutdown(flask_process)
            
            # Register exit handler
            cef.SetExitHandler(exit_handler)
            
            # Start CEF message loop (blocks until window is closed)
            logger.info("Starting CEF message loop")
            cef.MessageLoop()
            
            # Clean up on exit
            handle_shutdown(flask_process)
        
        logger.info("Application closed normally")
        return 0
        
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
