#!/usr/bin/env python
"""
Wrapper script to launch Flask application with proper path handling
"""
import os
import sys
import importlib.util
import traceback
import site

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
    
    # Check for venv site-packages in the resource directory
    site_packages_paths = [
        os.path.join(script_dir, 'venv', 'Lib', 'site-packages'),  # Windows
        os.path.join(script_dir, 'venv', 'lib', 'python3.9', 'site-packages'),  # Unix
    ]
    
    for site_pkg_path in site_packages_paths:
        if os.path.isdir(site_pkg_path):
            print(f"Adding site-packages path: {site_pkg_path}")
            site.addsitedir(site_pkg_path)
            if site_pkg_path not in sys.path:
                sys.path.insert(0, site_pkg_path)
    
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
    
    # List available modules for debugging
    try:
        print("\nChecking for essential modules:")
        modules_to_check = ['flask', 'sqlalchemy', 'pandas']
        for module_name in modules_to_check:
            try:
                module = importlib.import_module(module_name)
                print(f"  ✓ {module_name} found: {getattr(module, '__version__', 'unknown version')}")
            except ImportError as e:
                print(f"  ✗ {module_name} not found: {str(e)}")
    except Exception as e:
        print(f"Error checking modules: {str(e)}")
    
    try:
        # Import app.py as a module
        spec = importlib.util.spec_from_file_location("app_module", app_path)
        app_module = importlib.util.module_from_spec(spec)
        sys.modules["app_module"] = app_module
        spec.loader.exec_module(app_module)
        
        # Run the app if it has a main function or is runnable
        if hasattr(app_module, 'main'):
            print("Running app.main()")
            app_module.main()
        elif hasattr(app_module, 'app'):
            # Try to run the Flask app directly
            port = int(os.environ.get('PORT', 5000))
            host = os.environ.get('HOST', '127.0.0.1')
            print(f"Running Flask app on port {port}")
            app_module.app.run(host=host, port=port)
        else:
            print("ERROR: No app or main function found in app.py")
            sys.exit(1)
    except Exception as e:
        print("ERROR: Failed to run app.py")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
