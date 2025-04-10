"""
Build script for AMRS Maintenance Tracker Desktop Application
Creates a standalone executable for Windows using PyInstaller
"""
import os
import sys
import subprocess
import shutil
import argparse
import platform
import time
import json
from pathlib import Path

# Constants
APP_NAME = "AMRS Maintenance Tracker"
APP_VERSION = "1.0.0"
MAIN_SCRIPT = "desktop_app.py"
OUTPUT_DIR = "dist"
BUILD_DIR = "build"
ICON_FILE = "app_icon.ico"

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_step(step, text):
    """Print a step indicator"""
    print(f"\n[{step}] {text}")

def check_python_version():
    """Check if Python version is compatible"""
    print_step("CHECK", "Checking Python version...")
    
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print(f"Error: Python 3.7 or newer is required. Current version: {platform.python_version()}")
        return False
    
    print(f"✓ Using Python {platform.python_version()}")
    return True

def check_environment():
    """Check the environment for required tools"""
    print_step("CHECK", "Checking environment...")
    
    # Check if we're on Windows
    if platform.system() != "Windows":
        print(f"Warning: This build script is designed for Windows but detected {platform.system()}")
        if not input("Continue anyway? (y/N): ").lower().startswith('y'):
            return False
    
    # Check for pip
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], stdout=subprocess.PIPE)
        print("✓ pip is installed")
    except Exception:
        print("× pip not found. Please install pip.")
        return False
    
    return True

def install_dependencies(skip_deps=False):
    """Install required dependencies"""
    if skip_deps:
        print_step("SKIP", "Skipping dependency installation")
        return True
    
    print_step("INSTALL", "Installing required dependencies...")
    
    dependencies = [
        "cefpython3==66.1",
        "flask==2.2.5",
        "flask_sqlalchemy==3.0.5",
        "flask_login==0.6.2",
        "sqlalchemy==2.0.21",
        "pyinstaller==6.0.0",
        "requests==2.28.2"
    ]
    
    # Create requirements.txt
    with open("desktop_requirements.txt", "w") as f:
        f.write("\n".join(dependencies))
    
    # Install all dependencies at once
    try:
        process = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "desktop_requirements.txt"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ Dependencies installed successfully")
        if "-v" in sys.argv or "--verbose" in sys.argv:
            print(process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"× Error installing dependencies: {e}")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"× Unexpected error installing dependencies: {str(e)}")
        return False

def create_version_info():
    """Create version info file for Windows executable"""
    print_step("VERSION", "Creating version information...")
    
    version_parts = APP_VERSION.split('.')
    while len(version_parts) < 3:
        version_parts.append('0')
    
    version_tuple = ', '.join(version_parts + ['0'])
    
    # Using plain 'Copyright' text instead of the © symbol
    # to avoid encoding issues
    version_content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_tuple}),
    prodvers=({version_tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'AMRS'),
        StringStruct(u'FileDescription', u'{APP_NAME} Desktop Application'),
        StringStruct(u'FileVersion', u'{APP_VERSION}'),
        StringStruct(u'InternalName', u'{APP_NAME.replace(" ", "")}'),
        StringStruct(u'LegalCopyright', u'Copyright 2023 AMRS'),
        StringStruct(u'OriginalFilename', u'{APP_NAME.replace(" ", "")}.exe'),
        StringStruct(u'ProductName', u'{APP_NAME}'),
        StringStruct(u'ProductVersion', u'{APP_VERSION}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
    
    # Write the file with explicit encoding
    with open("file_version_info.txt", "w", encoding="utf-8") as f:
        f.write(version_content)
    
    print(f"✓ Created version info file")
    return True

def create_icon():
    """Create app icon if it doesn't exist"""
    if os.path.exists(ICON_FILE):
        print(f"✓ Using existing icon file: {ICON_FILE}")
        return True
    
    print_step("ICON", "Creating application icon...")
    
    # Check if PIL is installed for icon creation
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple icon
        img_size = 256
        img = Image.new('RGBA', (img_size, img_size), color=(254, 121, 0, 255))  # AMRS Orange
        draw = ImageDraw.Draw(img)
        
        # Add some simple graphics
        draw.rectangle(
            [(img_size//4, img_size//4), (3*img_size//4, 3*img_size//4)],
            outline='white',
            width=10
        )
        
        # Add text
        try:
            font = ImageFont.truetype("arial.ttf", 72)
        except IOError:
            font = ImageFont.load_default()
        
        draw.text(
            (img_size//2, img_size//2),
            "MT",
            fill='white',
            font=font,
            anchor="mm"
        )
        
        # Save as ICO
        img.save(ICON_FILE)
        print(f"✓ Created icon file: {ICON_FILE}")
        return True
    except ImportError:
        print("× PIL not found. Using default PyInstaller icon.")
        return True
    except Exception as e:
        print(f"× Error creating icon: {e}")
        print("  Using default PyInstaller icon.")
        return True

def create_spec_file(debug=False):
    """Create PyInstaller spec file"""
    print_step("SPEC", "Creating PyInstaller spec file...")
    
    # Calculate absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, MAIN_SCRIPT)
    icon_path = os.path.join(script_dir, ICON_FILE)
    
    # Convert paths to use forward slashes for the spec file
    main_script_path = main_script.replace('\\', '/')
    script_dir_path = script_dir.replace('\\', '/')
    icon_path_spec = icon_path.replace('\\', '/')
    
    # Check if icon exists
    icon_exists = os.path.exists(icon_path)
    
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(script_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    templates_dir_path = templates_dir.replace('\\', '/')
    
    # Create static directory if it doesn't exist
    static_dir = os.path.join(script_dir, "static")
    os.makedirs(static_dir, exist_ok=True)
    static_dir_path = static_dir.replace('\\', '/')
    
    # Path to app.py
    app_py_path = os.path.join(script_dir, "app.py").replace('\\', '/')
    
    # Path to models.py
    models_py_path = os.path.join(script_dir, "models.py").replace('\\', '/')
    
    # Generate spec content with properly formatted and closed parentheses
    debug_str = "True" if debug else "False"
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, get_package_paths

block_cipher = None

# Include all required data files
datas = []

# Include templates and static files
datas.extend([
    (r'{templates_dir_path}', 'templates'),
    (r'{static_dir_path}', 'static')
])

# Include Flask data files
datas.extend(collect_data_files('flask'))

# Include the app.py file
datas.append((r'{app_py_path}', '.'))

# Include models.py file
if os.path.exists(r'{models_py_path}'):
    datas.append((r'{models_py_path}', '.'))  # Fixed: properly closed parenthesis

# Bundle the application
a = Analysis(
    [r'{main_script_path}'],
    pathex=[r'{script_dir_path}'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'werkzeug',
        'sqlalchemy',
        'sqlalchemy.sql.default_comparator',
        'jinja2',
        'cefpython3',
        'requests'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{APP_NAME.replace(" ", "")}',
    debug={debug_str},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={debug_str},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={f"r'{icon_path_spec}'" if icon_exists else 'None'},
    version='file_version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{APP_NAME.replace(" ", "")}',
)
"""
    
    # Write spec file with explicit encoding
    spec_file = f"{os.path.splitext(MAIN_SCRIPT)[0]}.spec"
    with open(spec_file, "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print(f"✓ Created spec file: {spec_file}")
    return spec_file

def build_application(spec_file, debug=False):
    """Build the application using PyInstaller"""
    print_step("BUILD", f"Building {APP_NAME} application...")
    
    # Clean previous builds
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    
    # Run PyInstaller
    build_cmd = [sys.executable, "-m", "PyInstaller", spec_file]
    if debug:
        build_cmd.extend(["--log-level=DEBUG"])
    
    try:
        start_time = time.time()
        process = subprocess.run(
            build_cmd,
            check=True,
            capture_output=True,
            text=True
        )
        end_time = time.time()
        build_duration = end_time - start_time
        
        print(f"✓ Build completed in {build_duration:.1f} seconds")
        
        if debug or "-v" in sys.argv or "--verbose" in sys.argv:
            print(process.stdout)
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"× Error building application: Exit code {e.returncode}")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"× Unexpected error building application: {str(e)}")
        return False

def create_portable_marker():
    """Create a portable.txt marker in the dist directory"""
    print_step("PORTABLE", "Creating portable mode marker...")
    
    dist_path = os.path.join(OUTPUT_DIR, APP_NAME.replace(" ", ""))
    if not os.path.exists(dist_path):
        print("× Build directory not found. Skipping portable marker creation.")
        return False
        
    marker_path = os.path.join(dist_path, "portable.txt")
    
    try:
        with open(marker_path, "w") as f:
            f.write(f"{APP_NAME} v{APP_VERSION}\n")
            f.write("Portable Mode\n")
            f.write(f"Created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"✓ Created portable marker at {marker_path}")
        return True
    except Exception as e:
        print(f"× Error creating portable marker: {e}")
        return False

def create_config(server_url=None):
    """Create a configuration file for the application"""
    print_step("CONFIG", "Creating configuration file...")
    
    dist_path = os.path.join(OUTPUT_DIR, APP_NAME.replace(" ", ""))
    if not os.path.exists(dist_path):
        print("× Build directory not found. Skipping config creation.")
        return False
        
    config_path = os.path.join(dist_path, "app_config.json")
    
    config = {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "build_date": time.strftime('%Y-%m-%d %H:%M:%S'),
        "offline_mode": True,
        "debug": False
    }
    
    if server_url:
        config["server_url"] = server_url
        print(f"✓ Using pre-configured server URL: {server_url}")
    
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Created configuration file at {config_path}")
        return True
    except Exception as e:
        print(f"× Error creating configuration file: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description=f'Build {APP_NAME} Desktop Application')
    parser.add_argument('--debug', action='store_true', help='Build debug version with console')
    parser.add_argument('--skip-deps', action='store_true', help='Skip installing dependencies')
    parser.add_argument('--server-url', help='Pre-configure server URL')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show verbose output')
    parser.add_argument('--portable', action='store_true', help='Create portable version')
    args = parser.parse_args()
    
    print_header(f"Building {APP_NAME} v{APP_VERSION}")
    
    if not check_python_version():
        return 1
        
    if not check_environment():
        return 1
        
    if not install_dependencies(args.skip_deps):
        return 1
        
    if not create_version_info():
        return 1
        
    if not create_icon():
        # Not critical, continue anyway
        pass
        
    spec_file = create_spec_file(args.debug)
    if not spec_file:
        return 1
        
    if not build_application(spec_file, args.debug):
        return 1
    
    # If portable mode, create marker
    if args.portable:
        create_portable_marker()
    
    # Create config file
    create_config(args.server_url)
    
    dist_path = os.path.join(OUTPUT_DIR, APP_NAME.replace(" ", ""))
    exe_path = os.path.join(dist_path, f"{APP_NAME.replace(' ', '')}.exe")
    
    print_header("Build Successful!")
    print(f"Application built to: {os.path.abspath(dist_path)}")
    print(f"Executable: {os.path.abspath(exe_path)}")
    print("\nTo run the application:")
    print(f"  1. Navigate to {os.path.abspath(dist_path)}")
    print(f"  2. Run {APP_NAME.replace(' ', '')}.exe")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
