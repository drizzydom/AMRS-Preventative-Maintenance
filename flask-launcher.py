#!/usr/bin/env python
"""
Launcher script that fixes Python module imports
"""
import sys
import os
import importlib.util
import traceback

# Ensure working directory is the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create a more detailed debug log with clear filename
debug_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask-debug.log')
with open(debug_log_path, 'a') as f:
    f.write("\n\n========== FLASK LAUNCHER STARTED ==========\n")
    f.write(f"Date: {__import__('datetime').datetime.now()}\n")
    f.write(f"Python executable: {sys.executable}\n")
    f.write(f"Python version: {sys.version}\n")
    f.write(f"Working directory: {os.getcwd()}\n")
    f.write(f"Script path: {__file__}\n")
    
    # List all files in current directory
    f.write("\nFiles in current directory:\n")
    for file in os.listdir(os.getcwd()):
        f.write(f"- {file}\n")
    
    # List Python path
    f.write("\nPython path:\n")
    for p in sys.path:
        f.write(f"- {p}\n")

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
    
    # Debug: List files in current directory
    print("\nFiles in current directory:")
    try:
        for file in os.listdir(current_dir):
            print(f"- {file}")
    except Exception as e:
        print(f"Error listing directory contents: {e}")
    
    # Check for required files
    required_files = ['app.py', 'models.py', 'config.py']
    missing_files = [f for f in required_files if not os.path.exists(os.path.join(current_dir, f))]
    
    # Check for required directories
    required_dirs = ['static', 'templates']
    missing_dirs = [d for d in required_dirs if not os.path.isdir(os.path.join(current_dir, d))]
    
    # If any files or directories are missing, log and exit
    if missing_files or missing_dirs:
        error_msg = f"Missing required files/directories: {', '.join(missing_files + missing_dirs)}"
        print(f"ERROR: {error_msg}")
        with open(debug_log_path, 'a') as f:
            f.write(f"\nERROR: {error_msg}\n")
        sys.exit(2)
    
    # Import and run app.py using the corrected Python path
    try:
        print("Importing app module...")
        with open(debug_log_path, 'a') as f:
            f.write("\nAttempting to import app module...\n")
        
        import app
        
        with open(debug_log_path, 'a') as f:
            f.write("app module imported successfully!\n")
        
        # Set up port
        port = 5000
        if len(sys.argv) > 2 and sys.argv[1] == '--port':
            port = int(sys.argv[2])
            
        # Run the Flask application
        print(f"Starting Flask server on port {port}...")
        with open(debug_log_path, 'a') as f:
            f.write(f"Starting Flask server on port {port}...\n")
            
        try:
            app.app.run(host='127.0.0.1', port=port)
        except Exception as e:
            with open(debug_log_path, 'a') as f:
                f.write("Flask server failed to start\n")
                f.write(f"Date: {__import__('datetime').datetime.now()}\n")
                f.write(f"Python path: {sys.executable}\n")
                f.write(f"Flask script: {__file__}\n")
                f.write(f"Working directory: {os.getcwd()}\n")
                f.write(traceback.format_exc())
            raise
    except ImportError as e:
        with open(debug_log_path, 'a') as f:
            f.write(f"IMPORT ERROR: {e}\n")
            f.write(traceback.format_exc())
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
        with open(debug_log_path, 'a') as f:
            f.write(f"ERROR: {e}\n")
            f.write(traceback.format_exc())
        print(f"ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Top-level exception handler to catch anything that escapes main()
        with open(debug_log_path, 'a') as f:
            f.write(f"\nUNCAUGHT EXCEPTION: {e}\n")
            f.write(traceback.format_exc())
        print(f"UNCAUGHT EXCEPTION: {e}")
        traceback.print_exc()
        sys.exit(1)
