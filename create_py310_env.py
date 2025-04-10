"""
Script to set up a Python 3.10 virtual environment for AMRS Maintenance Tracker
"""
import os
import sys
import subprocess
import platform
import webbrowser
import ctypes
from pathlib import Path

# Python 3.10 download URLs
PYTHON_310_URLS = {
    'win32': 'https://www.python.org/ftp/python/3.10.11/python-3.10.11.exe',
    'win64': 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe',
    'macos': 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-macos11.pkg',
    'linux': 'https://www.python.org/downloads/release/python-31011/'
}

def is_admin():
    """Check if the script is running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def detect_python310():
    """Try to find Python 3.10 installation"""
    python_commands = [
        "python3.10",
        "py -3.10",
        "python3.10.exe",
        "py310",
        # Add paths for standard installation locations
        r"C:\Python310\python.exe",
        r"C:\Users\Dominic\AppData\Local\Programs\Python\Python310\python.exe",
        r"C:\Program Files\Python310\python.exe",
        r"C:\Program Files (x86)\Python310\python.exe",
    ]
    
    for cmd in python_commands:
        try:
            result = subprocess.run([cmd, "--version"], 
                                  capture_output=True, 
                                  text=True)
            if result.returncode == 0 and "Python 3.10" in result.stdout:
                print(f"✓ Found Python 3.10: {result.stdout.strip()}")
                print(f"  Command: {cmd}")
                return cmd
        except:
            continue
    
    return None

def get_download_url():
    """Get the appropriate Python 3.10 download URL for this system"""
    system = platform.system().lower()
    if system == 'windows':
        if platform.machine().endswith('64'):
            return PYTHON_310_URLS['win64']
        else:
            return PYTHON_310_URLS['win32']
    elif system == 'darwin':
        return PYTHON_310_URLS['macos']
    else:
        return PYTHON_310_URLS['linux']

def check_existing_venv():
    """Check if we have an existing venv_py310 folder"""
    venv_dir = Path("venv_py310")
    if venv_dir.exists():
        print(f"⚠️ Warning: {venv_dir} already exists.")
        response = input("Do you want to remove it and create a new one? (y/N): ")
        if response.lower() == 'y':
            import shutil
            try:
                shutil.rmtree(venv_dir)
                print(f"✓ Removed existing {venv_dir}")
                return True
            except Exception as e:
                print(f"Error: Could not remove {venv_dir}: {e}")
                print("Please close any applications that might be using it.")
                return False
        else:
            print("Using existing environment.")
            return True
    return True

def safe_pip_upgrade(pip_path):
    """Safely attempt to upgrade pip, but don't fail if it errors"""
    print("Attempting to upgrade pip (this step may be skipped if it fails)...")
    try:
        # Try to upgrade pip, but don't fail if it doesn't work
        subprocess.run([pip_path, "install", "--upgrade", "pip"], 
                      check=False,  # Don't raise exception on error
                      capture_output=True,
                      timeout=30)  # Add timeout to prevent hanging
        print("✓ Pip upgraded successfully")
        return True
    except Exception as e:
        print(f"Note: Pip upgrade skipped: {e}")
        print("This is not critical and we'll continue with installation.")
        return False

def install_requirements(pip_path, requirements_file):
    """Install requirements from a file"""
    print(f"Installing dependencies from {requirements_file}...")
    try:
        process = subprocess.run(
            [pip_path, "install", "-r", requirements_file],
            check=True,
            capture_output=True,
            text=True
        )
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: Exit code {e.returncode}")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("="*80)
    print("Python 3.10 Environment Setup for AMRS Maintenance Tracker")
    print("="*80)
    
    # Check for admin rights on Windows
    if platform.system() == "Windows" and not is_admin():
        print("Note: You're not running this script as Administrator.")
        print("Some operations may fail due to permission issues.")
        print("If you encounter errors, try running this script as Administrator.")
        print()
    
    # Check if Python 3.10 is installed
    python310 = detect_python310()
    
    if not python310:
        print("Python 3.10 not found. You need to install Python 3.10 first.")
        print("Download URL:", get_download_url())
        
        # Ask if the user wants to open the download page
        open_browser = input("Do you want to open the Python 3.10 download page? (y/N): ")
        if open_browser.lower() == 'y':
            webbrowser.open(get_download_url())
        
        print("\nAfter installing Python 3.10:")
        print("1. Make sure to check 'Add Python 3.10 to PATH' during installation")
        print("2. Run this script again")
        return 1
    
    # Check if we can proceed with existing venv
    if not check_existing_venv():
        return 1
    
    # Create virtual environment with Python 3.10
    venv_dir = "venv_py310"
    print(f"\nCreating Python 3.10 virtual environment in {venv_dir}...")
    
    try:
        # Create venv using the Python 3.10 command
        subprocess.run([python310, "-m", "venv", venv_dir], check=True)
        print("✓ Virtual environment created successfully")
        
        # Determine the pip and activation paths based on OS
        if platform.system() == "Windows":
            pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
            activate_path = os.path.join(venv_dir, "Scripts", "activate.bat")
        else:
            pip_path = os.path.join(venv_dir, "bin", "pip")
            activate_path = os.path.join(venv_dir, "bin", "activate")
        
        # Create requirements file
        requirements_file = "requirements_py310.txt"
        with open(requirements_file, "w") as f:
            f.write("""# Core dependencies - Python 3.10 compatible versions
flask==2.2.5
flask_sqlalchemy==3.0.5
flask_login==0.6.2
werkzeug==2.2.3
SQLAlchemy==2.0.21
Jinja2==3.1.2

# CEF Python - critical for desktop app
cefpython3==66.1

# Build tools
pyinstaller==6.0.0

# Utilities & extra dependencies
requests==2.28.2
python-dotenv==1.0.0
PyJWT==2.8.0
""")
        
        # Try to upgrade pip but don't fail if it doesn't work
        safe_pip_upgrade(pip_path)
        
        # Install requirements
        if not install_requirements(pip_path, requirements_file):
            print("\nError installing dependencies. You can try manually:")
            print(f"1. Activate environment: {activate_path}")
            print(f"2. Install packages: {pip_path} install -r {requirements_file}")
            return 1
        
        print("\n"+"="*80)
        print("Python 3.10 Environment Setup Complete!")
        print("="*80)
        
        # Show activation command
        if platform.system() == "Windows":
            activate_cmd = f"{venv_dir}\\Scripts\\activate"
        else:
            activate_cmd = f"source {venv_dir}/bin/activate"
        
        print(f"\nTo activate the Python 3.10 environment:")
        print(f"    {activate_cmd}")
        
        print("\nAfter activation, run:")
        print("    python desktop_app.py")
        
        print("\nTo build the desktop application:")
        print("    python build_desktop_app.py --portable")
        
        return 0
        
    except Exception as e:
        print(f"\nError setting up environment: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
