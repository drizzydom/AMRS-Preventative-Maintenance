#!/usr/bin/env python
"""
Check and fix configuration files for the AMRS Electron app
"""
import os
import sys
import json
import sqlite3
import subprocess
import shutil
import traceback
import importlib
import platform
from pathlib import Path

def check_file_exists(file_path):
    """Check if a file exists"""
    exists = os.path.exists(file_path)
    print(f"File: {file_path} - {'FOUND' if exists else 'MISSING'}")
    return exists

def inspect_package_json():
    """Check package.json configuration"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    package_path = os.path.join(script_dir, 'package.json')
    
    if not check_file_exists(package_path):
        return False
    
    try:
        with open(package_path, 'r') as f:
            data = json.load(f)
        
        print("\nPackage.json configuration:")
        print(f"- Name: {data.get('name', 'MISSING')}")
        print(f"- Main: {data.get('main', 'MISSING')}")
        print(f"- Build scripts:")
        for script_name, script_command in data.get('scripts', {}).items():
            print(f"  - {script_name}: {script_command}")
        
        build_config = data.get('build', {})
        print(f"- Build configuration:")
        print(f"  - appId: {build_config.get('appId', 'MISSING')}")
        print(f"  - productName: {build_config.get('productName', 'MISSING')}")
        
        # Check extraResources
        print("- Extra resources:")
        for resource in build_config.get('extraResources', []):
            print(f"  - {resource.get('from', 'MISSING')} -> {resource.get('to', 'MISSING')}")
        
        return True
    except Exception as e:
        print(f"Error inspecting package.json: {e}")
        return False

def check_electron_config():
    """Check electron configuration files"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    electron_dir = os.path.join(script_dir, 'electron_app')
    
    # Check main.js
    main_js_path = os.path.join(electron_dir, 'main.js')
    preload_js_path = os.path.join(electron_dir, 'preload.js')
    
    print("\nElectron configuration:")
    check_file_exists(main_js_path)
    check_file_exists(preload_js_path)
    
    # Check if electron_app directory exists
    if os.path.isdir(electron_dir):
        print(f"- electron_app directory: FOUND")
        print(f"- Contents of electron_app:")
        for item in os.listdir(electron_dir):
            item_path = os.path.join(electron_dir, item)
            item_type = 'DIR ' if os.path.isdir(item_path) else 'FILE'
            print(f"  - {item_type}: {item}")
    else:
        print(f"- electron_app directory: MISSING")

def check_python_config():
    """Check Python configuration files"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\nPython configuration:")
    app_py_path = os.path.join(script_dir, 'app.py')
    requirements_path = os.path.join(script_dir, 'requirements.txt')
    
    check_file_exists(app_py_path)
    check_file_exists(requirements_path)
    
    # Check electron-related Python files
    electron_files = [
        'electron_config.py',
        'electron_db_setup.py',
        'electron_db_sync.py',
        'electron_api.py',
        'electron_sqlite_setup.py',
        'offline_adapter.py'
    ]
    
    print("- Electron Python modules:")
    for file in electron_files:
        check_file_exists(os.path.join(script_dir, file))
    
    # Check our debug/launcher files
    debug_files = [
        'app-launcher.py',
        'python_env_debug.py',
        'install_dependencies.py',
        'simple_flask_launcher.py'
    ]
    
    print("- Debug/launcher files:")
    for file in debug_files:
        check_file_exists(os.path.join(script_dir, file))
    
    # Check if Python is available
    try:
        result = subprocess.run([sys.executable, '--version'], 
                               capture_output=True, text=True)
        print(f"- Python version: {result.stdout.strip()}")
    except Exception as e:
        print(f"- Error checking Python version: {e}")

def check_python_environment():
    """Check Python environment and modules"""
    print("\nPython Environment:")
    print(f"- Python executable: {sys.executable}")
    print(f"- Python version: {platform.python_version()}")
    print(f"- System: {platform.system()} {platform.release()}")
    
    # Check sys.path
    print("\n- Python path:")
    for i, path in enumerate(sys.path):
        exists = os.path.exists(path)
        print(f"  {i+1}. {path} {'✓' if exists else '✗'}")
    
    # Check for required modules
    print("\n- Required modules:")
    required_modules = [
        'flask', 
        'sqlalchemy', 
        'jinja2', 
        'werkzeug', 
        'dotenv',
        'cryptography'
    ]
    
    missing_modules = []
    for module_name in required_modules:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'unknown version')
            print(f"  ✓ {module_name}: {version}")
        except ImportError as e:
            print(f"  ✗ {module_name}: {str(e)}")
            missing_modules.append(module_name)
    
    # Try to install missing modules
    if missing_modules:
        print("\n- Attempting to install missing modules:")
        for module in missing_modules:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])
                print(f"  ✓ Installed {module}")
            except Exception as e:
                print(f"  ✗ Failed to install {module}: {str(e)}")
    
    return len(missing_modules) == 0

def check_database_config():
    """Check database configuration"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\nDatabase configuration:")
    
    # Check for SQLite database files
    sqlite_db_path = os.path.join(script_dir, 'amrs_maintenance.db')
    if check_file_exists(sqlite_db_path):
        try:
            # Try to open the database
            conn = sqlite3.connect(sqlite_db_path)
            cursor = conn.cursor()
            
            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"- SQLite database tables:")
            for table in tables:
                print(f"  - {table[0]}")
            
            conn.close()
        except Exception as e:
            print(f"- Error inspecting SQLite database: {e}")
    
    # Check electron_config.py for database URI
    electron_config_path = os.path.join(script_dir, 'electron_config.py')
    if os.path.exists(electron_config_path):
        try:
            with open(electron_config_path, 'r') as f:
                content = f.read()
                
            # Look for database URI definition
            if 'get_database_uri' in content:
                print("- Database URI function found in electron_config.py")
            else:
                print("- Database URI function NOT found in electron_config.py")
        except Exception as e:
            print(f"- Error reading electron_config.py: {e}")

def check_resource_directories():
    """Check resource directories"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\nResource directories:")
    
    # Check for static and templates directories
    static_dir = os.path.join(script_dir, 'static')
    templates_dir = os.path.join(script_dir, 'templates')
    
    if check_file_exists(static_dir) and os.path.isdir(static_dir):
        print(f"- Static directory contains {len(os.listdir(static_dir))} files/directories")
    
    if check_file_exists(templates_dir) and os.path.isdir(templates_dir):
        print(f"- Templates directory contains {len(os.listdir(templates_dir))} files/directories")
    
    # Check for site-packages directory
    site_packages_dir = os.path.join(script_dir, 'site-packages')
    if check_file_exists(site_packages_dir) and os.path.isdir(site_packages_dir):
        print(f"- site-packages directory contains {len(os.listdir(site_packages_dir))} files/directories")
        
        # Check for key packages
        key_packages = ['flask', 'werkzeug', 'sqlalchemy', 'jinja2']
        for pkg in key_packages:
            pkg_dir = os.path.join(site_packages_dir, pkg)
            if os.path.exists(pkg_dir):
                print(f"  - {pkg}: FOUND")
            else:
                # Check for alternate naming patterns
                found = False
                for item in os.listdir(site_packages_dir):
                    if item.lower().startswith(pkg.lower()):
                        print(f"  - {pkg}: FOUND as {item}")
                        found = True
                        break
                if not found:
                    print(f"  - {pkg}: MISSING")

def main():
    """Main entry point for the configuration checker"""
    print("=" * 50)
    print("AMRS Electron App - Configuration Checker")
    print("=" * 50)
    
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Run all checks
    inspect_package_json()
    check_electron_config()
    check_python_config()
    check_python_environment()
    check_database_config()
    check_resource_directories()
    
    print("\nConfiguration check complete.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unhandled error: {e}")
        traceback.print_exc()
