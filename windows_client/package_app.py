import os
import sys
import shutil
from pathlib import Path
import PyInstaller.__main__

def package_application():
    """Package the application with PyInstaller"""
    print("Packaging Maintenance Tracker Client...")
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    
    # Clean up previous build files
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            
    # Define icon path
    icon_path = Path(script_dir, 'app_icon.ico')
    if not icon_path.exists():
        print("Warning: App icon not found at", icon_path)
        icon_path = None
    
    # Create PyInstaller command arguments
    args = [
        'main.py',
        '--name=MaintenanceTrackerClient',
        '--onefile',
        '--windowed',
        '--add-data=LICENSE;.',
        '--log-level=INFO',
    ]
    
    # Add icon if available
    if icon_path:
        args.append(f'--icon={icon_path}')
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print("Packaging complete!")
    print("Executable created at:", Path(script_dir, 'dist', 'MaintenanceTrackerClient.exe'))

if __name__ == "__main__":
    package_application()
