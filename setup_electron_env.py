"""
Setup script for the Electron + Flask environment
This script helps create the correct virtual environment and install dependencies
"""
import os
import sys
import subprocess
import platform

def run_command(command, cwd=None):
    """Run a command and print its output"""
    print(f"\n> {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, text=True)
    return result.returncode == 0

def find_python():
    """Find an appropriate Python executable"""
    python_executables = [
        "python3.9",
        "python39",
        "python3",
        "python",
        r"C:\Python39\python.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python39\python.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Python39\python.exe"),
    ]
    
    for python in python_executables:
        try:
            # Check if this Python is available and get its version
            version_cmd = f'"{python}" -c "import sys; print(sys.version)"'
            result = subprocess.run(version_cmd, shell=True, text=True, capture_output=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                if "3.9" in version:
                    print(f"Found Python 3.9: {python} ({version})")
                    return python
                else:
                    print(f"Found Python {version}, but need 3.9")
        except Exception:
            pass
    
    return None

def setup_virtual_env():
    """Set up the virtual environment"""
    # Create paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(base_dir, "venv_py39_electron")
    
    # Find Python 3.9
    python = find_python()
    if not python:
        print("\nERROR: Could not find Python 3.9. Please install it first.")
        print("Download from: https://www.python.org/downloads/release/python-3913/")
        return False
    
    # Create virtual environment
    if not os.path.exists(venv_dir):
        print(f"\nCreating virtual environment in {venv_dir}...")
        if not run_command(f'"{python}" -m venv "{venv_dir}"'):
            print("Failed to create virtual environment.")
            return False
    
    # Activate and install dependencies
    if platform.system() == "Windows":
        pip = os.path.join(venv_dir, "Scripts", "pip")
    else:
        pip = os.path.join(venv_dir, "bin", "pip")
    
    # Install Python dependencies
    print("\nInstalling Python dependencies...")
    packages = [
        "flask",
        "flask-sqlalchemy",
        "flask-login",
        "flask-mail",  # Added for email support
        "flask-cors",
        "psutil",
        "pyinstaller",
        "werkzeug==2.2.3",  # Specific version for compatibility
        "Jinja2==3.1.2",
        "SQLAlchemy==2.0.21",
        "python-dotenv==1.0.0",
        "PyJWT==2.8.0",
        "bleach==6.0.0",
        "itsdangerous==2.1.2",
        "click==8.1.7"
    ]
    
    # Install pip and setuptools first to avoid issues
    if not run_command(f'"{pip}" install --upgrade pip setuptools wheel'):
        print("Failed to upgrade pip, setuptools, and wheel.")
        return False
        
    if not run_command(f'"{pip}" install -U {" ".join(packages)}'):
        print("Failed to install Python packages.")
        return False
        
    # Try to install any missing packages from requirements.txt if it exists
    req_file = os.path.join(base_dir, "requirements.txt")
    if os.path.exists(req_file):
        print("\nInstalling dependencies from requirements.txt...")
        if not run_command(f'"{pip}" install -r "{req_file}"'):
            print("Warning: Some packages from requirements.txt may not have installed properly.")
            print("Continuing with setup...")
    
    # Check for Node.js
    print("\nChecking for Node.js...")
    has_node = run_command("node --version")
    has_npm = run_command("npm --version")
    
    if not has_node or not has_npm:
        print("\nWARNING: Node.js or npm not found. Please install Node.js from:")
        print("https://nodejs.org/en/download/ (LTS version recommended)")
        return False
    
    # Initialize npm project if package.json doesn't exist
    package_json = os.path.join(base_dir, "package.json")
    if not os.path.exists(package_json):
        print("\nInitializing npm project...")
        electron_dir = os.path.join(base_dir, "electron_app")
        os.makedirs(electron_dir, exist_ok=True)
        
        if not run_command("npm init -y", electron_dir):
            print("Failed to initialize npm project.")
            return False
    
    # Create required icons directory and placeholder icons
    electron_dir = os.path.join(base_dir, "electron_app")
    icons_dir = os.path.join(electron_dir, "icons")
    os.makedirs(icons_dir, exist_ok=True)
    
    # Generate a simple tray icon if it doesn't exist
    tray_icon_path = os.path.join(icons_dir, "tray-icon.png")
    app_icon_path = os.path.join(icons_dir, "app.ico")
    
    if not os.path.exists(tray_icon_path) or not os.path.exists(app_icon_path):
        print("\nGenerating placeholder icons...")
        try:
            # Try to use PIL to create basic icons if available
            try:
                from PIL import Image, ImageDraw
                
                # Create tray icon (16x16 px)
                img = Image.new('RGBA', (16, 16), color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                # Draw a blue square with rounded corners
                draw.rectangle([0, 0, 15, 15], fill=(65, 105, 225), outline=(255, 255, 255))
                img.save(tray_icon_path)
                print(f"Created tray icon: {tray_icon_path}")
                
                # Create app icon (256x256 px)
                img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                # Draw a blue square with rounded corners
                draw.rectangle([0, 0, 255, 255], fill=(65, 105, 225), outline=(255, 255, 255))
                # Save as .ico for Windows
                img.save(app_icon_path.replace('.ico', '.png'))
                # For .ico format, we'll use a simple binary file as fallback
                with open(app_icon_path, 'wb') as f:
                    f.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x20\x00\x68\x04\x00\x00\x16\x00\x00\x00')
                    f.write(b'\x28\x00\x00\x00\x10\x00\x00\x00\x20\x00\x00\x00\x01\x00\x20\x00\x00\x00\x00\x00\x00\x00')
                    # Simple 16x16 blue icon data
                    for i in range(256):
                        f.write(b'\x41\x69\xE1\xFF')
                print(f"Created app icon: {app_icon_path}")
            except ImportError:
                # If PIL is not available, create simple binary files
                print("PIL not available. Creating basic placeholder icons...")
                # Create a simple 1x1 blue PNG for the tray icon
                with open(tray_icon_path, 'wb') as f:
                    # Minimal valid PNG file with blue color
                    png_header = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63fcffff3f030000050001f451d2a00000000049454e44ae426082')
                    f.write(png_header)
                
                # Create a simple .ico file (just the header)
                with open(app_icon_path, 'wb') as f:
                    f.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x20\x00\x68\x04\x00\x00\x16\x00\x00\x00')
                    f.write(b'\x28\x00\x00\x00\x10\x00\x00\x00\x20\x00\x00\x00\x01\x00\x20\x00\x00\x00\x00\x00\x00\x00')
                    # Simple 16x16 blue icon data
                    for i in range(256):
                        f.write(b'\x41\x69\xE1\xFF')
        except Exception as e:
            print(f"Warning: Could not create icon files: {str(e)}")
            print("You'll need to manually create icon files:")
            print(f"1. Create {tray_icon_path}")
            print(f"2. Create {app_icon_path}")
    
    # Install Electron dependencies
    print("\nInstalling Electron dependencies...")
    electron_deps = [
        "electron@latest",
        "electron-builder@latest",
        "wait-on@latest",
        "concurrently@latest",
        "cross-env@latest"
    ]
    
    if not run_command(f"npm install --save-dev {' '.join(electron_deps)}", electron_dir):
        print("Failed to install Electron dependencies.")
        return False
    
    print("\n✓ Setup completed successfully!")
    print(f"\nTo activate the virtual environment:")
    if platform.system() == "Windows":
        print(f"   {venv_dir}\\Scripts\\activate")
    else:
        print(f"   source {venv_dir}/bin/activate")
    
    return True

if __name__ == "__main__":
    if not setup_virtual_env():
        sys.exit(1)
