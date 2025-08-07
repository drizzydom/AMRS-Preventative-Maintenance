#!/usr/bin/env python3
"""
Python Environment Bundler for Electron App
This script creates a portable Python environment for the AMRS Maintenance Tracker
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)
    return result

import subprocess
import sys
import os
import platform

def bundle_python_environment():
    """Create a portable Python environment for the current platform"""
    
    platform_name = platform.system().lower()
    print(f"[BUNDLE] Creating Python environment for {platform_name}")
    
    # Check Python version - use 3.11.0 which has been tested and works properly
    python_version = sys.version_info
    print(f"[BUNDLE] Using Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Ensure we're using Python 3.11.0 for consistency with testing environment
    if python_version.major != 3 or python_version.minor != 11:
        print(f"[BUNDLE] WARNING: Expected Python 3.11.x but got {python_version.major}.{python_version.minor}.{python_version.micro}")
        print(f"[BUNDLE] This may cause compatibility issues with the tested environment")
    else:
        print(f"[BUNDLE] ✅ Python 3.11.{python_version.micro} - compatible with testing environment")
    
    # Create virtual environment
    venv_path = "python"
    if os.path.exists(venv_path):
        print(f"[BUNDLE] Removing existing environment: {venv_path}")
        import shutil
        shutil.rmtree(venv_path)
    
    print(f"[BUNDLE] Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
    
    # Determine pip path based on platform
    if platform_name == "windows":
        pip_path = os.path.join(venv_path, "Scripts", "pip")
        python_path = os.path.join(venv_path, "Scripts", "python")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
        python_path = os.path.join(venv_path, "bin", "python")
    
    print(f"[BUNDLE] Installing requirements...")
    subprocess.run([pip_path, "install", "-r", "requirements-electron.txt"], check=True)
    
    print(f"[BUNDLE] Python environment created successfully at: {venv_path}")
    print(f"[BUNDLE] Python executable: {python_path}")
    
    # Verify the bundled Python version
    result = subprocess.run([python_path, "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        bundled_version = result.stdout.strip()
        print(f"[BUNDLE] Bundled Python version: {bundled_version}")
    else:
        print(f"[BUNDLE] Warning: Could not verify bundled Python version")
    
    return True
    
def create_macos_python(python_dir):
    """Create portable Python for macOS"""
    print("🍎 Creating macOS Python environment...")
    
    # Create virtual environment
    run_command([sys.executable, "-m", "venv", str(python_dir)])
    
    # Install requirements
    pip_path = python_dir / "bin" / "pip"
    run_command([str(pip_path), "install", "--upgrade", "pip"])
    run_command([str(pip_path), "install", "-r", "requirements-electron.txt"])
    
    # Create a startup script
    startup_script = python_dir / "run_app.py"
    startup_script.write_text('''#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

# Change to app directory
os.chdir(app_dir)

# Import and run the app
import app
''')
    startup_script.chmod(0o755)

def create_windows_python(python_dir):
    """Create portable Python for Windows"""
    print("🪟 Creating Windows Python environment...")
    
    # Create virtual environment
    run_command([sys.executable, "-m", "venv", str(python_dir)])
    
    # Install requirements
    pip_path = python_dir / "Scripts" / "pip.exe"
    run_command([str(pip_path), "install", "--upgrade", "pip"])
    run_command([str(pip_path), "install", "-r", "requirements-electron.txt"])
    
    # Create a startup script
    startup_script = python_dir / "run_app.py"
    startup_script.write_text('''#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

# Change to app directory
os.chdir(app_dir)

# Import and run the app
import app
''')

def create_linux_python(python_dir):
    """Create portable Python for Linux"""
    print("🐧 Creating Linux Python environment...")
    
    # Create virtual environment
    run_command([sys.executable, "-m", "venv", str(python_dir)])
    
    # Install requirements
    pip_path = python_dir / "bin" / "pip"
    run_command([str(pip_path), "install", "--upgrade", "pip"])
    run_command([str(pip_path), "install", "-r", "requirements-electron.txt"])
    
    # Create a startup script
    startup_script = python_dir / "run_app.py"
    startup_script.write_text('''#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

# Change to app directory
os.chdir(app_dir)

# Import and run the app
import app
''')
    startup_script.chmod(0o755)

if __name__ == "__main__":
    print("🐍 Creating portable Python environment for AMRS Maintenance Tracker...")
    bundle_python_environment()
