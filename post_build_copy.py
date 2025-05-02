import os
import shutil
import subprocess
import sys
import platform
import logging
import urllib.request
import zipfile
import tempfile
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'post_build_copy.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("Running post-build file copy to ensure all required files are present...")

# Get the resources directory in the packaged app
ELECTRON_DIR = os.path.join(os.path.dirname(__file__), 'electron_app')
RESOURCES_DIR = os.path.join(ELECTRON_DIR, 'dist', 'win-unpacked', 'resources')
VENV_SCRIPTS_DIR = os.path.join(RESOURCES_DIR, 'venv', 'Scripts')

# Create the resources directory if it doesn't exist
if not os.path.exists(RESOURCES_DIR):
    logger.warning(f"Resources directory not found at {RESOURCES_DIR}, creating it")
    os.makedirs(RESOURCES_DIR, exist_ok=True)

# Create the venv Scripts directory if it doesn't exist
if not os.path.exists(VENV_SCRIPTS_DIR):
    logger.warning(f"Venv Scripts directory not found at {VENV_SCRIPTS_DIR}, creating it")
    os.makedirs(VENV_SCRIPTS_DIR, exist_ok=True)

# Source directory (project root)
SOURCE_DIR = os.path.dirname(__file__)

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

# Directories that must be copied with all their contents
REQUIRED_DIRS = [
    'static',
    'templates',
    'instance',
    'modules'
]

# Copy required files
copied_files = []
for file in REQUIRED_FILES:
    src = os.path.join(SOURCE_DIR, file)
    dst = os.path.join(RESOURCES_DIR, file)
    if os.path.exists(src):
        logger.info(f"Copying {file} to resources directory")
        try:
            shutil.copy2(src, dst)
            copied_files.append(file)
            logger.info(f"Successfully copied {file}")
        except Exception as e:
            logger.error(f"Error copying {file}: {e}")
    else:
        logger.warning(f"Warning: {file} not found in source directory at {src}")

# Copy required directories
copied_dirs = []
for dir_name in REQUIRED_DIRS:
    src_dir = os.path.join(SOURCE_DIR, dir_name)
    dst_dir = os.path.join(RESOURCES_DIR, dir_name)
    
    if os.path.exists(src_dir):
        logger.info(f"Copying directory {dir_name} to resources")
        try:
            # Remove the destination directory if it exists to ensure clean copy
            if os.path.exists(dst_dir):
                shutil.rmtree(dst_dir)
            
            # Copy the directory recursively
            shutil.copytree(src_dir, dst_dir)
            copied_dirs.append(dir_name)
            logger.info(f"Successfully copied directory {dir_name}")
        except Exception as e:
            logger.error(f"Error copying directory {dir_name}: {e}")
    else:
        logger.warning(f"Warning: Directory {dir_name} not found at {src_dir}")

# Verify static directory exists in source
static_dir = os.path.join(SOURCE_DIR, 'static')
if not os.path.exists(static_dir):
    logger.error(f"CRITICAL: Static directory not found at {static_dir}")
    # List the contents of the source directory to help diagnose
    logger.info(f"Contents of source directory {SOURCE_DIR}:")
    for item in os.listdir(SOURCE_DIR):
        logger.info(f"- {item}")

# ENHANCED WEASYPRINT SUPPORT: Ensure GTK DLLs are included
logger.info("Ensuring WeasyPrint GTK dependencies are included...")

# Path to local DLLs (if they exist)
LOCAL_DLLS_DIR = os.path.join(SOURCE_DIR, 'dependencies', 'weasyprint-dlls')

# Check for local DLLs first
if os.path.exists(LOCAL_DLLS_DIR) and os.listdir(LOCAL_DLLS_DIR):
    logger.info(f"Found local DLLs in {LOCAL_DLLS_DIR}")
    # Copy all DLLs from the local directory to the Scripts directory
    dll_count = 0
    for file in os.listdir(LOCAL_DLLS_DIR):
        if file.lower().endswith('.dll'):
            src = os.path.join(LOCAL_DLLS_DIR, file)
            dst = os.path.join(VENV_SCRIPTS_DIR, file)
            logger.info(f"Copying {file} to Scripts directory")
            shutil.copy2(src, dst)
            dll_count += 1
    
    if dll_count > 0:
        logger.info(f"Successfully copied {dll_count} DLLs from local directory")
    else:
        logger.warning("No DLL files found in local directory, falling back to download")
else:
    logger.info("No local DLLs found, attempting to download WeasyPrint dependencies")
    
    # Try downloading from multiple sources
    success = False
    
    # List of download URLs to try (most recent first)
    urls = [
        "https://github.com/Kozea/WeasyPrint/releases/download/v60.2/weasyprint-64.zip",
        "https://github.com/Kozea/WeasyPrint/releases/download/v60.1/weasyprint-64.zip", 
        "https://github.com/Kozea/WeasyPrint/releases/download/v60.0/weasyprint-64.zip",
        "https://github.com/Kozea/WeasyPrint/releases/download/v59.0/weasyprint-64.zip"
    ]
    
    # Try each URL until one works
    for url in urls:
        try:
            logger.info(f"Trying to download from: {url}")
            # Create a temporary file for the zip
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                deps_zip = temp_file.name
            
            # Download the file
            urllib.request.urlretrieve(url, deps_zip)
            
            logger.info(f"Download successful from {url}")
            
            # Extract the zip
            with zipfile.ZipFile(deps_zip, 'r') as zip_ref:
                # Extract to the Scripts directory
                logger.info(f"Extracting DLLs to {VENV_SCRIPTS_DIR}")
                zip_ref.extractall(VENV_SCRIPTS_DIR)
            
            # Clean up the zip file
            os.remove(deps_zip)
            
            # Also save these DLLs to the local directory for future builds
            os.makedirs(LOCAL_DLLS_DIR, exist_ok=True)
            for file in os.listdir(VENV_SCRIPTS_DIR):
                if file.lower().endswith('.dll'):
                    src = os.path.join(VENV_SCRIPTS_DIR, file)
                    dst = os.path.join(LOCAL_DLLS_DIR, file)
                    # Only copy if the file doesn't already exist
                    if not os.path.exists(dst):
                        shutil.copy2(src, dst)
            
            success = True
            break
        except Exception as e:
            logger.error(f"Error with {url}: {e}")

# List DLLs in the Scripts directory
dll_count = 0
try:
    logger.info("DLLs in Scripts directory:")
    for f in os.listdir(VENV_SCRIPTS_DIR):
        if f.lower().endswith('.dll'):
            logger.info(f"  - {f}")
            dll_count += 1
    
    if dll_count > 0:
        logger.info(f"Successfully ensured {dll_count} DLLs in the build")
    else:
        logger.error("No DLLs were found or installed! PDF generation will not work.")
except Exception as e:
    logger.error(f"Error listing DLLs: {e}")

# Verify the build
logger.info("\nPost-build verification:")
logger.info(f"Successfully copied {len(copied_files)} files:")
for file in copied_files:
    logger.info(f"  - {file}")

logger.info(f"Successfully copied {len(copied_dirs)} directories:")
for dir_name in copied_dirs:
    logger.info(f"  - {dir_name}")

logger.info(f"Successfully included {dll_count} WeasyPrint DLLs")

logger.info("Post-build copy process completed")