#!/usr/bin/env python3
"""
Build script for creating Windows executable
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import zipfile

APP_NAME = "Maintenance Tracker"
APP_VERSION = "1.0.0"

def run_command(command):
    """Run a shell command and print output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, check=True)
    return result

def create_executable():
    """Create executable with PyInstaller"""
    print(f"Building {APP_NAME} v{APP_VERSION}...")
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        run_command("pip install pyinstaller")
    
    # Clean previous build
    dist_dir = Path("dist")
    build_dir = Path("build")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Create executable
    cmd = [
        "pyinstaller",
        "--name", f"{APP_NAME.replace(' ', '')}",
        "--onefile",
        "--windowed",
        "--clean",
        # "--add-data", "assets;assets",  # Uncomment if you have assets
        "main.py"
    ]
    
    run_command(" ".join(cmd))
    
    print("Build completed successfully!")

def create_installer():
    """Create installer with NSIS"""
    # Check if NSIS is installed
    nsis_path = ""
    
    # Common installation paths for NSIS
    possible_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            nsis_path = path
            break
    
    if not nsis_path:
        print("NSIS not found. Skipping installer creation.")
        print("You can download NSIS from https://nsis.sourceforge.io/Download")
        return False
    
    print("Creating installer with NSIS...")
    
    # Write NSIS script
    nsis_script = f"""
    !define APP_NAME "{APP_NAME}"
    !define APP_VERSION "{APP_VERSION}"
    !define APP_EXE "{APP_NAME.replace(' ', '')}.exe"
    
    Name "${{APP_NAME}} ${{APP_VERSION}}"
    OutFile "dist/{APP_NAME.replace(' ', '')}Setup.exe"
    InstallDir "$PROGRAMFILES\\{APP_NAME}"
    
    # Default section
    Section
        SetOutPath $INSTDIR
        
        # Create program directory and copy files
        CreateDirectory $INSTDIR
        File "dist\\${{APP_EXE}}"
        
        # Create shortcut in start menu
        CreateDirectory "$SMPROGRAMS\\{APP_NAME}"
        CreateShortcut "$SMPROGRAMS\\{APP_NAME}\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
        
        # Create shortcut on desktop
        CreateShortcut "$DESKTOP\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
        
        # Create uninstaller
        WriteUninstaller "$INSTDIR\\uninstall.exe"
    SectionEnd
    
    # Uninstaller section
    Section "Uninstall"
        Delete "$INSTDIR\\${{APP_EXE}}"
        Delete "$INSTDIR\\uninstall.exe"
        RMDir "$INSTDIR"
        
        # Remove shortcuts
        Delete "$SMPROGRAMS\\{APP_NAME}\\${{APP_NAME}}.lnk"
        RMDir "$SMPROGRAMS\\{APP_NAME}"
        Delete "$DESKTOP\\${{APP_NAME}}.lnk"
    SectionEnd
    """
    
    # Write NSIS script to file
    with open("installer.nsi", "w") as f:
        f.write(nsis_script)
    
    # Run NSIS
    run_command(f'"{nsis_path}" installer.nsi')
    
    # Clean up script
    os.remove("installer.nsi")
    
    print(f"Installer created: dist/{APP_NAME.replace(' ', '')}Setup.exe")
    return True

def create_portable_zip():
    """Create portable ZIP package"""
    print("Creating portable ZIP package...")
    
    # Create portable directory
    portable_dir = Path("dist") / f"{APP_NAME.replace(' ', '')}_Portable"
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    portable_dir.mkdir(exist_ok=True)
    
    # Copy executable
    shutil.copy(
        Path("dist") / f"{APP_NAME.replace(' ', '')}.exe", 
        portable_dir / f"{APP_NAME.replace(' ', '')}.exe"
    )
    
    # Create README file
    with open(portable_dir / "README.txt", "w") as f:
        f.write(f"""
{APP_NAME} {APP_VERSION} - Portable Edition

This is the portable version of {APP_NAME}. Just run the executable to start the application.

Note: Application settings will be stored in your user directory.
""")
    
    # Create ZIP file
    zip_path = Path("dist") / f"{APP_NAME.replace(' ', '')}_Portable_{APP_VERSION}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in portable_dir.glob("**/*"):
            zipf.write(file, file.relative_to(portable_dir))
    
    print(f"Portable ZIP created: {zip_path}")

def main():
    create_executable()
    create_installer()
    create_portable_zip()

if __name__ == "__main__":
    main()
