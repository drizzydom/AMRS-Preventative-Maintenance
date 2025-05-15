#!/usr/bin/env python
"""
Direct application launcher for Electron - bypasses diagnostic mode
"""
import os
import sys
import traceback
import importlib.util
from datetime import datetime

def write_status_files(port):
    """Write signal files for Electron"""
    try:
        status_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'AMRS-Maintenance-Tracker')
        os.makedirs(status_dir, exist_ok=True)
        
        # Write the port file
        port_file = os.path.join(status_dir, 'flask_port.txt')
        with open(port_file, 'w') as f:
            f.write(str(port))
        print(f"Wrote port {port} to {port_file}")
        
        # Write the ready file
        signal_file = os.path.join(status_dir, 'flask_ready.txt')
        with open(signal_file, 'w') as f:
            f.write(f"Flask fully running with MAIN APP on port {port} at {datetime.now().isoformat()}")
        print(f"Created signal file at {signal_file}")
    except Exception as e:
        print(f"Warning: Could not create status files: {e}")

def run_main_app():
    """Run the main Flask application directly"""
    try:
        # Get the app directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(script_dir, 'app.py')
        
        if not os.path.exists(app_path):
            print(f"Error: Main app not found at {app_path}")
            return False
            
        print(f"Loading main app from: {app_path}")
        
        # Import the app.py file
        spec = importlib.util.spec_from_file_location("app_module", app_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        if not hasattr(app_module, 'app'):
            print("Error: No 'app' object found in app.py")
            return False
            
        # Get the Flask app object
        app = app_module.app
        
        # Configure for Electron if needed
        if hasattr(app, 'config'):
            app.config['ELECTRON'] = True
            
        # Get the port
        port = int(os.environ.get('PORT', 8033))
        print(f"Running main app on port {port}")
        
        # Write status files before starting the app
        write_status_files(port)
        
        # Run the app
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        return True
    except Exception as e:
        print(f"Error running main app: {e}")
        print(traceback.format_exc())
        return False
        
if __name__ == "__main__":
    print("=" * 60)
    print("AMRS Maintenance Tracker - Direct Application Launcher")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Arguments: {sys.argv}")
    
    run_main_app()
