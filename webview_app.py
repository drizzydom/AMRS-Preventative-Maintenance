#!/usr/bin/env python
"""
AMRS Maintenance Tracker - Windows WebView2 Application
This script launches a native Windows application with WebView2
that loads the Flask application
"""

import os
import sys
import time
import threading
import logging
import argparse
import webview
import requests
import subprocess
from pathlib import Path
import shutil
import pathlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[WEBVIEW] %(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("webview_app")

# Application configuration
APP_TITLE = "AMRS Maintenance Tracker"
FLASK_PORT = 10000
FLASK_URL = f"http://localhost:{FLASK_PORT}"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'img', 'favicon.ico')
BOOTSTRAP_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_bootstrap.py')

# Flask process
flask_process = None

def is_port_in_use(port):
    """Check if the port is already in use"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_flask():
    """Start the Flask server in a subprocess"""
    global flask_process
    
    logger.info(f"Starting Flask application on port {FLASK_PORT}")
    
    # Check if the port is already in use
    if is_port_in_use(FLASK_PORT):
        logger.info(f"Port {FLASK_PORT} is already in use, assuming Flask is running")
        return True
    
    # Start the Flask app using app_bootstrap.py or app_bootstrap.exe
    try:
        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller bundle
            # First try to find app_bootstrap.exe in the main dist folder
            exe_dir = os.path.dirname(sys.executable)
            
            # Check multiple possible locations for app_bootstrap.exe
            possible_paths = [
                os.path.abspath(os.path.join(exe_dir, 'app_bootstrap', 'app_bootstrap.exe')),  # inside app_bootstrap subfolder
                os.path.abspath(os.path.join(os.path.dirname(exe_dir), 'app_bootstrap', 'app_bootstrap.exe')),  # parallel to webview_app folder
                os.path.abspath(os.path.join(exe_dir, '..', 'app_bootstrap', 'app_bootstrap.exe')),  # up one level
                os.path.abspath(os.path.join(exe_dir, '..', '..', 'app_bootstrap')),  # up two levels
                os.path.abspath(os.path.join(exe_dir, 'app_bootstrap.exe'))  # directly in same folder
            ]
            
            bootstrap_exe = None
            for path in possible_paths:
                logger.info(f"[WEBVIEW] Checking for app_bootstrap.exe at: {path}")
                if os.path.exists(path):
                    bootstrap_exe = path
                    logger.info(f"[WEBVIEW] Found app_bootstrap.exe at: {bootstrap_exe}")
                    break
            
            if not bootstrap_exe:
                # Last resort: search the disk
                logger.info("[WEBVIEW] Searching for app_bootstrap.exe in parent directories...")
                current_dir = exe_dir
                max_levels = 5  # Don't search too high up
                for _ in range(max_levels):
                    app_bootstrap_dir = os.path.join(current_dir, 'app_bootstrap')
                    if os.path.exists(app_bootstrap_dir):
                        bootstrap_exe = os.path.join(app_bootstrap_dir, 'app_bootstrap.exe')
                        if os.path.exists(bootstrap_exe):
                            logger.info(f"[WEBVIEW] Found app_bootstrap.exe at: {bootstrap_exe}")
                            break
                    # Move up one directory
                    parent_dir = os.path.dirname(current_dir)
                    if parent_dir == current_dir:  # Reached root directory
                        break
                    current_dir = parent_dir
            
            if not bootstrap_exe:
                logger.error("app_bootstrap.exe not found in any expected location")
                raise RuntimeError("app_bootstrap.exe not found in any expected location")
                
            cmd = [bootstrap_exe, '--port', str(FLASK_PORT)]
        else:
            python_exe = sys.executable
            bootstrap_script = BOOTSTRAP_SCRIPT
            cmd = [python_exe, bootstrap_script, '--port', str(FLASK_PORT)]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Start process with output redirected to PIPE
        flask_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Start a thread to read and log the output
        def log_output():
            for line in iter(flask_process.stdout.readline, ''):
                logger.info(f"[FLASK] {line.rstrip()}")
        
        threading.Thread(target=log_output, daemon=True).start()
        
        # Wait for Flask to start
        logger.info("Waiting for Flask to start...")
        max_retries = 30
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.get(f"{FLASK_URL}/health-check", timeout=1)
                if response.status_code == 200:
                    logger.info("Flask application is running")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            retry_count += 1
            time.sleep(1)
        
        logger.error(f"Flask application failed to start after {max_retries} seconds")
        return False
    
    except Exception as e:
        logger.error(f"Error starting Flask application: {e}")
        return False

def shutdown_flask():
    """Shutdown the Flask server subprocess"""
    global flask_process
    if flask_process:
        logger.info("Shutting down Flask application")
        try:
            # Try to terminate gracefully
            flask_process.terminate()
            flask_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If it doesn't shut down, kill it
            logger.warning("Flask application did not terminate gracefully, killing process")
            flask_process.kill()
        
        flask_process = None

def on_closed():
    """Handle window closed event"""
    logger.info("WebView window closed")
    shutdown_flask()

def on_shown():
    """Handle window shown event"""
    logger.info("WebView window shown")

def on_new_window(url):
    """Handle new window requests (e.g., print view) by opening inside the app"""
    logger.info(f"Opening new window for URL: {url}")
    webview.create_window('Print View', url)

def wait_for_flask(url, timeout=60):
    """Wait for Flask to be ready"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def start_app():
    """Start the application with splash screen"""
    # Get splash screen HTML path
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        splash_path = os.path.join(exe_dir, 'static', 'splash.html')
        if not os.path.exists(splash_path):
            splash_path = os.path.abspath(os.path.join('static', 'splash.html'))
    else:
        splash_path = os.path.abspath(os.path.join('static', 'splash.html'))
    logger.info(f"[WEBVIEW] Final splash path: {splash_path} (exists: {os.path.exists(splash_path)})")

    # Create a splash window that will be replaced with the main window
    splash_html = ''
    if os.path.exists(splash_path):
        with open(splash_path, 'r') as f:
            splash_html = f.read()
    else:
        splash_html = '<html><body style="background-color: #333; color: white; font-family: Arial; display: flex; align-items: center; justify-content: center;"><h1>AMRS Maintenance Tracker</h1><p>Loading...</p></body></html>'

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Show splash window
    splash_window = webview.create_window('Loading...', html=splash_html, width=600, height=400, resizable=False, frameless=True)
    
    def on_shown():
        logger.info("[WEBVIEW] Splash screen shown, waiting for Flask...")
        
        def check_flask_ready():
            if wait_for_flask(f'http://localhost:{FLASK_PORT}/health-check'):
                logger.info("[WEBVIEW] Flask is ready, switching to main window.")
                # Create the main window
                main_window = webview.create_window(APP_TITLE, FLASK_URL, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
                # Destroy splash window after a slight delay to ensure main window is visible
                def destroy_splash():
                    time.sleep(0.5)
                    splash_window.destroy()
                threading.Thread(target=destroy_splash, daemon=True).start()
            else:
                logger.error("[WEBVIEW] Flask did not start in time, showing error.")
                splash_window.destroy()
                webview.create_window('Error', html='<h1>Failed to start backend</h1>')
        
        # Check Flask in a background thread to avoid blocking UI
        threading.Thread(target=check_flask_ready, daemon=True).start()
    
    # Register the shown event handler
    splash_window.events.shown += on_shown
    
    logger.info("[WEBVIEW] Starting webview event loop with manual splash screen...")
    webview.start(gui='edgechromium', debug=True)

if __name__ == "__main__":
    start_app()