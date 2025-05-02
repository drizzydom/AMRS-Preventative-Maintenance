import os
import shutil
import subprocess
import sys

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

print("\nList of files in resources directory after copy:")
for item in os.listdir(RESOURCES_DIR):
    item_path = os.path.join(RESOURCES_DIR, item)
    if os.path.isdir(item_path):
        print(f"- [DIR] {item}")
    else:
        print(f"- [FILE] {item}")

print("\nPost-build file copy completed!")