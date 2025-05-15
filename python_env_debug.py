#!/usr/bin/env python
"""
Debug helper for the packaged Python environment
"""
import os
import sys
import importlib
import site
import pkgutil
import traceback
import time

def log_path_info():
    """Log Python path and environment info"""
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"sys.path:")
    for i, p in enumerate(sys.path):
        print(f"  {i}: {p}")
    
    print("\nEnvironment variables:")
    for key, value in sorted(os.environ.items()):
        print(f"  {key}={value}")

def list_available_modules():
    """List all available modules in the current environment"""
    print("\nAvailable modules:")
    
    modules = sorted([name for _, name, ispkg in pkgutil.iter_modules()
                      if not name.startswith('_')])
    
    # Print in columns
    col_width = 25
    num_cols = 3
    rows = [modules[i:i + num_cols] for i in range(0, len(modules), num_cols)]
    
    for row in rows:
        print('  ' + ''.join(name.ljust(col_width) for name in row))

def check_required_modules():
    """Check if required modules can be imported"""
    required_modules = [
        'flask', 
        'sqlalchemy', 
        'pandas', 
        'jinja2', 
        'werkzeug', 
        'dotenv',
        'cryptography'
    ]
    
    print("\nChecking required modules:")
    for module_name in required_modules:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'unknown version')
            print(f"  ✓ {module_name}: {version}")
        except ImportError as e:
            print(f"  ✗ {module_name}: {str(e)}")
            sys.path_importer_cache.clear()
            importlib.invalidate_caches()
            # Try alternative paths for the module
            try:
                # Add common site-packages paths if not already in sys.path
                script_dir = os.path.dirname(os.path.abspath(__file__))
                possible_site_pkg_paths = [
                    os.path.join(script_dir, 'venv', 'Lib', 'site-packages'),
                    os.path.join(script_dir, 'venv', 'lib', 'python3.9', 'site-packages'),
                ]
                
                found = False
                for site_pkg in possible_site_pkg_paths:
                    if os.path.exists(site_pkg) and site_pkg not in sys.path:
                        site.addsitedir(site_pkg)
                        print(f"  Added path: {site_pkg}")
                        # Try importing again
                        module = importlib.import_module(module_name)
                        version = getattr(module, '__version__', 'unknown version')
                        print(f"  ✓ {module_name}: {version} (after path fix)")
                        found = True
                        break
                
                if not found:
                    print(f"  Module not found in alternative paths")
            except Exception as e2:
                print(f"  Failed to import from alternative paths: {str(e2)}")

def main():
    print("=" * 80)
    print("AMRS Electron App - Python Environment Debugger")
    print("=" * 80)
    
    log_path_info()
    check_required_modules()
    list_available_modules()
    
    print("\nScript directory structure:")
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Contents of {script_dir}:")
        for item in sorted(os.listdir(script_dir)):
            item_path = os.path.join(script_dir, item)
            item_type = 'dir ' if os.path.isdir(item_path) else 'file'
            print(f"  {item_type}: {item}")
        
        # Check venv structure
        venv_path = os.path.join(script_dir, 'venv')
        if os.path.exists(venv_path):
            print(f"\nVirtual environment structure at {venv_path}:")
            for root, dirs, files in os.walk(venv_path, topdown=True, onerror=None):
                level = root.replace(script_dir, '').count(os.sep)
                indent = ' ' * 2 * level
                if level <= 3:  # Limit recursion depth for readability
                    print(f"{indent}{os.path.basename(root)}/")
                    if level == 3:
                        print(f"{indent}  ...")  # Abbreviate deeper levels
                    else:
                        for d in dirs:
                            print(f"{indent}  {d}/")
                        for f in files[:5]:  # Show only first 5 files
                            print(f"{indent}  {f}")
                        if len(files) > 5:
                            print(f"{indent}  ... and {len(files)-5} more files")
    except Exception as e:
        print(f"Error analyzing directory structure: {str(e)}")
        traceback.print_exc()
    
    # Keep console open in case we're running as a subprocess
    print("\nDebug information collection complete.")
    print("Press Ctrl+C to exit...")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
