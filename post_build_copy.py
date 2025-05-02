import os
import shutil
import subprocess
import sys
import platform

print("Running post-build file copy to ensure all required files are present...")

# Get the resources directory in the packaged app
RESOURCES_DIR = os.path.join(os.path.dirname(__file__), 'dist', 'win-unpacked', 'resources')

if not os.path.exists(RESOURCES_DIR):
    print(f"Resources directory not found at {RESOURCES_DIR}")
    sys.exit(1)

# Files that must be copied to the root of the resources directory
REQUIRED_FILES = [
    'app.py',
    'models.py',
    'config.py',
    'auto_migrate.py',
    'expand_user_fields.py',
    'db_config.py',
    'cache_config.py',
    'simple_healthcheck.py',
    'api_endpoints.py',
    'excel_importer.py',
    'notification_scheduler.py',
    'wsgi.py',
    'requirements.txt',
    'flask-launcher.py',
    'install_weasyprint_windows_deps.py'
]

# Directories that must be copied
REQUIRED_DIRS = [
    'static',
    'templates',
    'instance',
    'modules'
]

# Copy required files
copied_files = []
for file in REQUIRED_FILES:
    src = os.path.join(os.path.dirname(__file__), file)
    dst = os.path.join(RESOURCES_DIR, file)
    if os.path.exists(src):
        print(f"Copying {file} to resources directory")
        shutil.copy2(src, dst)
        copied_files.append(file)
    else:
        print(f"Warning: {file} not found in source directory")

# Copy required directories
copied_dirs = []
for dir_name in REQUIRED_DIRS:
    src = os.path.join(os.path.dirname(__file__), dir_name)
    dst = os.path.join(RESOURCES_DIR, dir_name)
    if os.path.exists(src):
        print(f"Copying directory {dir_name} to resources directory")
        if os.path.exists(dst):
            print(f"Removing existing directory: {dst}")
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        copied_dirs.append(dir_name)
    else:
        print(f"Warning: Directory {dir_name} not found in source directory")
        # Create empty directory
        os.makedirs(dst, exist_ok=True)

# Create an empty instance directory if it doesn't exist
instance_dir = os.path.join(RESOURCES_DIR, 'instance')
os.makedirs(instance_dir, exist_ok=True)

# Create a flask-debug.log file for startup debugging
with open(os.path.join(RESOURCES_DIR, 'flask-debug.log'), 'w') as f:
    f.write("Flask debug log created by post_build_copy.py\n")
    f.write(f"Date: {__import__('datetime').datetime.now()}\n")
    f.write(f"Copied files: {', '.join(copied_files)}\n")
    f.write(f"Copied directories: {', '.join(copied_dirs)}\n")

# Ensure the Python venv has all required packages
print("\n===== Verifying Python packages in the venv =====")
venv_dir = os.path.join(RESOURCES_DIR, 'venv')
if not os.path.exists(venv_dir):
    print("Creating venv directory")
    os.makedirs(venv_dir, exist_ok=True)

# Determine the Python executable path inside the venv
if platform.system() == "Windows":
    venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
    venv_pip = os.path.join(venv_dir, "Scripts", "pip.exe")
else:
    venv_python = os.path.join(venv_dir, "bin", "python")
    venv_pip = os.path.join(venv_dir, "bin", "pip")

venv_scripts_dir = os.path.join(venv_dir, "Scripts" if platform.system() == "Windows" else "bin")
os.makedirs(venv_scripts_dir, exist_ok=True)

# Check if the venv exists and has a Python executable
if not os.path.exists(venv_python):
    print(f"Creating a new venv at {venv_dir}")
    try:
        # Try to copy the existing venv
        source_venv = os.path.join(os.path.dirname(__file__), 'venv_py39_electron')
        if os.path.exists(source_venv):
            print(f"Copying existing venv from {source_venv}")
            # Only copy new files to avoid overwriting existing ones
            for root, dirs, files in os.walk(source_venv):
                for dir_name in dirs:
                    src_dir = os.path.join(root, dir_name)
                    rel_path = os.path.relpath(src_dir, source_venv)
                    dst_dir = os.path.join(venv_dir, rel_path)
                    os.makedirs(dst_dir, exist_ok=True)
                
                for file_name in files:
                    src_file = os.path.join(root, file_name)
                    rel_path = os.path.relpath(src_file, source_venv)
                    dst_file = os.path.join(venv_dir, rel_path)
                    if not os.path.exists(dst_file):
                        try:
                            # Create the directory if needed
                            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                            shutil.copy2(src_file, dst_file)
                        except Exception as e:
                            print(f"Error copying {src_file}: {e}")
        else:
            print("No existing venv to copy, must create a new one")
            # Create python/pip script files
            with open(venv_python, 'w') as f:
                f.write("# Placeholder for Python executable\n")
            with open(venv_pip, 'w') as f:
                f.write("# Placeholder for pip executable\n")
    except Exception as e:
        print(f"Error creating venv: {e}")

# Install packages if requirements.txt exists
req_file = os.path.join(RESOURCES_DIR, 'requirements.txt')
if os.path.exists(req_file):
    print(f"Installing packages from {req_file}")
    
    # Create a .env file to ensure packages are installed in the correct location
    env_file = os.path.join(RESOURCES_DIR, '.env')
    with open(env_file, 'w') as f:
        f.write(f"PYTHONPATH={RESOURCES_DIR}\n")
    
    # Create a batch file to install the packages
    install_script = os.path.join(RESOURCES_DIR, 'install_packages.bat')
    with open(install_script, 'w') as f:
        f.write(f"""@echo off
echo Installing packages from requirements.txt
cd /d "{RESOURCES_DIR}"
set PYTHONPATH={RESOURCES_DIR}

REM Try to find a system Python to create the venv
where python > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Found system Python, using it to create venv
    python -m venv venv
) else (
    echo Python not found in PATH, trying Python 3.9
    where python3.9 > nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo Found Python 3.9, using it to create venv
        python3.9 -m venv venv
    ) else (
        echo Python 3.9 not found, trying common locations
        if exist "C:\\Python39\\python.exe" (
            echo Found Python 3.9 in C:\\Python39
            "C:\\Python39\\python.exe" -m venv venv
        ) else if exist "%LOCALAPPDATA%\\Programs\\Python\\Python39\\python.exe" (
            echo Found Python 3.9 in %%LOCALAPPDATA%%\\Programs\\Python\\Python39
            "%LOCALAPPDATA%\\Programs\\Python\\Python39\\python.exe" -m venv venv
        ) else (
            echo Python not found, cannot create venv
            exit /b 1
        )
    )
)

REM Install packages
echo Installing packages with pip
venv\\Scripts\\pip install --no-cache-dir -r requirements.txt
echo Packages installed successfully
""")
    
    try:
        print("Running package installation script")
        subprocess.run(install_script, shell=True, check=True)
        print("Packages installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        print("Warning: Flask and other required packages may not be available in the packaged app")
else:
    print("Warning: requirements.txt not found, skipping package installation")

print("\nList of files in resources directory after copy:")
for item in os.listdir(RESOURCES_DIR):
    item_path = os.path.join(RESOURCES_DIR, item)
    if os.path.isdir(item_path):
        print(f"- [DIR] {item}")
    else:
        print(f"- [FILE] {item}")

print("\nPost-build file copy completed!")