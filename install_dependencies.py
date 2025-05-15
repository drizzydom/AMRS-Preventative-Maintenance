#!/usr/bin/env python
"""
Module installer for the packaged app
"""
import os
import sys
import subprocess
import importlib
import site
import time

def get_pip_path():
    """Get path to pip executable"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # We're in a virtual environment
        if sys.platform == 'win32':
            return os.path.join(sys.prefix, 'Scripts', 'pip.exe')
        else:
            return os.path.join(sys.prefix, 'bin', 'pip')
    else:
        # System Python
        if sys.platform == 'win32':
            return os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pip.exe')
        else:
            return os.path.join(os.path.dirname(sys.executable), 'bin', 'pip')

def run_pip_install(package):
    """Install a package using pip"""
    pip_path = get_pip_path()
    print(f"Installing {package} using {pip_path}...")
    
    try:
        subprocess.check_call([pip_path, 'install', package])
        print(f"Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")
        return False
    except Exception as e:
        print(f"Unknown error installing {package}: {e}")
        return False

def check_dependencies():
    """Check and install required dependencies"""
    required_packages = [
        'flask==2.2.3',
        'werkzeug==2.2.3',
        'sqlalchemy',
        'pandas',
        'jinja2',
        'python-dotenv',
        'flask-login',
        'flask-sqlalchemy',
        'cryptography'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        package_name = package.split('==')[0]
        try:
            importlib.import_module(package_name.lower())
            print(f"✓ {package_name} is already installed")
        except ImportError:
            print(f"✗ {package_name} is missing")
            missing_packages.append(package)
    
    # Install missing packages
    if missing_packages:
        print(f"\nInstalling {len(missing_packages)} missing packages...")
        for package in missing_packages:
            run_pip_install(package)
        
        # Refresh sys.path to include newly installed packages
        script_dir = os.path.dirname(os.path.abspath(__file__))
        site_packages_paths = [
            os.path.join(script_dir, 'venv', 'Lib', 'site-packages'),
            os.path.join(script_dir, 'venv', 'lib', 'python3.9', 'site-packages'),
        ]
        
        for site_pkg in site_packages_paths:
            if os.path.exists(site_pkg) and site_pkg not in sys.path:
                site.addsitedir(site_pkg)
                print(f"Added site-packages path: {site_pkg}")
        
        print("Refreshed Python package paths")
    else:
        print("\nAll required packages are installed")

def main():
    print("=" * 80)
    print("AMRS Electron App - Dependencies Installer")
    print("=" * 80)
    
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    check_dependencies()
    
    print("\nDependency check complete")

if __name__ == "__main__":
    main()
