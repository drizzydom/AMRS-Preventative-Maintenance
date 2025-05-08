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
    
    # Start the Flask app using app_bootstrap.py
    try:
        cmd = [sys.executable, BOOTSTRAP_SCRIPT, '--port', str(FLASK_PORT)]
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

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description=f"{APP_TITLE} Windows Application")
    parser.add_argument('--url', default=None, help='URL to load (for debugging)')
    args = parser.parse_args()
    
    logger.info(f"Starting {APP_TITLE} WebView2 application")
    
    # Start Flask application
    if not args.url:
        if not start_flask():
            logger.error("Could not start Flask application, exiting")
            return 1
    
    # Configure the window
    webview_url = args.url or FLASK_URL
    logger.info(f"Opening WebView2 with URL: {webview_url}")
    
    # Create the window
    try:
        window = webview.create_window(
            title=APP_TITLE,
            url=webview_url,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            min_size=(800, 600),
            confirm_close=True,
            text_select=True
        )
        
        # Set event handlers
        window.events.closed += on_closed
        window.events.shown += on_shown
        
        # Start the WebView2 main loop
        webview.start(debug=True)
        
    except Exception as e:
        logger.error(f"Error creating WebView2 window: {e}")
        shutdown_flask()
        return 1
    
    logger.info("Application exited normally")
    return 0

if __name__ == "__main__":
    sys.exit(main())