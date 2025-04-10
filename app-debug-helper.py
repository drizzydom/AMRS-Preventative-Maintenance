"""
Helper script to debug app.py in packaged environment
"""
import os
import sys
import traceback

def debug_app():
    """Run diagnostic checks for app packaging"""
    # Print environment info
    print("=== Environment Information ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Check for critical files
    print("\n=== Checking Critical Files ===")
    app_path = os.path.join(os.getcwd(), 'app.py')
    if os.path.exists(app_path):
        print(f"app.py: Found at {app_path}")
        with open(app_path, 'r', encoding='utf-8') as f:
            first_lines = [f.readline() for _ in range(5)]
        print("First 5 lines:")
        print(''.join(first_lines))
    else:
        print(f"app.py: MISSING at {app_path}")
    
    # Check for directories
    print("\n=== Checking Directories ===")
    directories = ['static', 'templates', 'modules']
    for directory in directories:
        dir_path = os.path.join(os.getcwd(), directory)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            files = os.listdir(dir_path)
            print(f"{directory}: Found with {len(files)} files")
            if files:
                print(f"Sample files: {', '.join(files[:5])}")
        else:
            print(f"{directory}: MISSING")
    
    # Check for Flask
    print("\n=== Checking Flask ===")
    try:
        import flask
        print(f"Flask version: {flask.__version__}")
        print(f"Flask location: {flask.__file__}")
    except ImportError as e:
        print(f"Failed to import Flask: {e}")
    
    # Check other dependencies
    print("\n=== Checking Other Dependencies ===")
    dependencies = [
        'pandas', 'werkzeug', 'jinja2', 'click', 'itsdangerous'
    ]
    
    for dep in dependencies:
        try:
            module = __import__(dep)
            if hasattr(module, '__version__'):
                print(f"{dep}: {module.__version__}")
            else:
                print(f"{dep}: Imported successfully, but no version info")
        except ImportError as e:
            print(f"{dep}: Import failed - {e}")
    
    # Save directory listing
    print("\n=== Saving Directory Listing ===")
    try:
        with open('resources-files.txt', 'w') as f:
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if not file.endswith('.pyc') and '__pycache__' not in root:
                        f.write(os.path.join(root, file) + '\n')
        print("Directory listing saved to resources-files.txt")
    except Exception as e:
        print(f"Error saving directory listing: {e}")

if __name__ == "__main__":
    print("Running app.py diagnostics...")
    try:
        debug_app()
        print("\nDiagnostics completed successfully")
    except Exception as e:
        print(f"Error during diagnostics: {e}")
        traceback.print_exc()
    
    print("\nPress Enter to exit...")
    try:
        input()
    except:
        pass
