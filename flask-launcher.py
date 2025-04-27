#!/usr/bin/env python
"""
Launcher script that fixes Python module imports
"""
import sys
import os
import importlib.util
import traceback

# Ensure the current directory is in sys.path so auto_migrate.py can be found
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def main():
    """Main function that runs the Flask app with proper module imports"""
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the current directory to Python path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print(f"Added {current_dir} to Python path")
    
    # Print diagnostics
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    
    # Import and run app.py using the corrected Python path
    try:
        print("Importing app module...")
        import app
        
        # Set up port
        port = 5000
        if len(sys.argv) > 2 and sys.argv[1] == '--port':
            port = int(sys.argv[2])
            
        # Run the Flask application
        print(f"Starting Flask server on port {port}...")
        app.app.run(host='127.0.0.1', port=port)
    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
        traceback.print_exc()
        
        # Try to diagnose module import issues
        if "models" in str(e):
            print("\nTrying to locate models.py...")
            for path in [current_dir, os.getcwd()]:
                models_path = os.path.join(path, 'models.py')
                if os.path.exists(models_path):
                    print(f"Found models.py at: {models_path}")
                    
                    # Try manual import to see if it works
                    try:
                        spec = importlib.util.spec_from_file_location("models", models_path)
                        models = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(models)
                        print("Successfully imported models manually!")
                        
                        # Add its directory to sys.path
                        models_dir = os.path.dirname(models_path)
                        if models_dir not in sys.path:
                            sys.path.insert(0, models_dir)
                            print(f"Added {models_dir} to path and retrying...")
                            import app
                            app.app.run(host='127.0.0.1', port=port)
                            return
                    except Exception as e2:
                        print(f"Failed to import models manually: {e2}")
                else:
                    print(f"models.py not found at: {models_path}")
            
            # List all .py files to help troubleshoot
            print("\nAvailable Python files:")
            for root, dirs, files in os.walk(current_dir):
                for file in files:
                    if file.endswith('.py'):
                        print(os.path.join(root, file))
        
        # Exit with error code
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
