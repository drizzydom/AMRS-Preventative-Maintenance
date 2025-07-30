#!/usr/bin/env python
"""
Wrapper script to launch Flask application with proper path handling
"""
import os
import sys
import importlib.util
import traceback

def main():
    """Main entry point for the application."""
    # Print diagnostics
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")
    
    # Add the script directory to path if not already there
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # Look for app.py in current directory and script directory
    app_paths = [
        os.path.join(os.getcwd(), 'app.py'),
        os.path.join(script_dir, 'app.py')
    ]
    
    # Find app.py
    app_path = None
    for path in app_paths:
        if os.path.isfile(path):
            app_path = path
            print(f"Found app.py at: {path}")
            break
    
    if not app_path:
        print("ERROR: app.py not found!")
        print(f"Searched paths: {app_paths}")
        sys.exit(1)
    
    try:
        # Import app.py as a module
        spec = importlib.util.spec_from_file_location("app_module", app_path)
        app_module = importlib.util.module_from_spec(spec)
        sys.modules["app_module"] = app_module
        spec.loader.exec_module(app_module)
        
        # Run app if it has a main function or app.run()
        if hasattr(app_module, 'main'):
            print("Running app.main()")
            app_module.main()
        elif hasattr(app_module, 'app'):
            port = 5000
            if len(sys.argv) > 2 and sys.argv[1] == '--port':
                port = int(sys.argv[2])
            
            print(f"Running Flask app on port {port}")
            app_module.app.run(host='127.0.0.1', port=port, debug=False)
        else:
            print("ERROR: No app or main function found in app.py")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load or run app.py: {e}")
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()
