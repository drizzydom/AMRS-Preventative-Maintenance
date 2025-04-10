"""
Simplified build script for AMRS Maintenance Tracker desktop application
Designed to overcome PyInstaller bytecode analysis issues
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

APP_NAME = "AMRS Maintenance Tracker"
MAIN_SCRIPT = "desktop_app.py"

def clean_build_directories():
    """Clean previous build directories to avoid cached issues"""
    print("Cleaning build directories...")
    build_dirs = ['build', 'dist', '__pycache__']
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_name)
    
    # Remove any existing spec files
    for spec_file in Path('.').glob('*.spec'):
        print(f"Removing {spec_file}...")
        os.unlink(spec_file)

def create_direct_command():
    """Create a direct PyInstaller command that bypasses module analysis issues"""
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--clean',                     # Clean PyInstaller cache
        '--noconfirm',                 # Overwrite output directory without asking
        '--name', APP_NAME.replace(' ', ''),
        '--add-data', 'templates;templates',
        '--add-data', 'static;static',
        '--hidden-import', 'flask',
        '--hidden-import', 'flask_sqlalchemy',
        '--hidden-import', 'flask_login',
        '--hidden-import', 'sqlalchemy',
        '--hidden-import', 'jinja2',
        '--hidden-import', 'werkzeug',
        '--hidden-import', 'sqlite3',
        '--hidden-import', 'signal',
        # Exclude problematic modules
        '--exclude-module', '_tkinter',
        '--exclude-module', 'matplotlib',
        '--exclude-module', 'PIL',
        # Runtime options
        '--onedir',                     # Create a directory containing the executable
        '--windowed',                   # Windows app without console (use --console for debug)
        MAIN_SCRIPT
    ]
    
    # Add app.py and models.py as data files
    if os.path.exists("app.py"):
        cmd.extend(['--add-data', 'app.py;.'])
    if os.path.exists("models.py"):
        cmd.extend(['--add-data', 'models.py;.'])
        
    return cmd

def run_pyinstaller(cmd):
    """Run PyInstaller with the given command"""
    print("\nRunning PyInstaller with command:")
    print(" ".join(cmd))
    print("\n" + "=" * 80)
    
    try:
        process = subprocess.run(cmd, check=True)
        print("\nBuild completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error code: {e.returncode}")
        return False

def main():
    print("=" * 80)
    print(f"Simple Build Script for {APP_NAME}")
    print("=" * 80)
    
    # Clean up previous builds
    clean_build_directories()
    
    # Create and run PyInstaller command
    cmd = create_direct_command()
    success = run_pyinstaller(cmd)
    
    if success:
        output_dir = os.path.join('dist', APP_NAME.replace(' ', ''))
        print(f"\nApplication built successfully!")
        print(f"Output directory: {os.path.abspath(output_dir)}")
        print(f"Run the application by executing: {os.path.join(output_dir, APP_NAME.replace(' ', '')+'.exe')}")
        return 0
    else:
        print("\nBuild failed. Try the following options:")
        print("1. Try running with the --debug flag: python simple_build.py --debug")
        print("2. Check for dependency issues")
        print("3. Look for compatibility problems between packages")
        return 1

if __name__ == "__main__":
    # Add --debug option to create a console application for debugging
    if "--debug" in sys.argv:
        print("Building in DEBUG mode with console window...")
        debug_cmd = create_direct_command()
        # Replace --windowed with --console
        if "--windowed" in debug_cmd:
            debug_cmd.remove("--windowed")
        debug_cmd.append("--console")
        run_pyinstaller(debug_cmd)
    else:
        sys.exit(main())
