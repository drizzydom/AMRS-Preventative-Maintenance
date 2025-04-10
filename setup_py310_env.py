"""
Setup script to create a Python 3.10 virtual environment
and install all required dependencies
"""
import os
import sys
import subprocess
import platform

def main():
    print("="*80)
    print("AMRS Maintenance Tracker - Python 3.10 Environment Setup")
    print("="*80)
    print("This script will create a virtual environment with Python 3.10")
    print("and install all required dependencies.")
    
    # Check if Python 3.10 is available
    try:
        # Try different possible commands for Python 3.10
        commands = ["python3.10", "py -3.10", "python3.10.exe", "py3.10"]
        python_cmd = None
        
        for cmd in commands:
            try:
                result = subprocess.run([cmd, "--version"], 
                                       capture_output=True, 
                                       text=True)
                if result.returncode == 0 and "Python 3.10" in result.stdout:
                    python_cmd = cmd
                    print(f"Found Python 3.10: {result.stdout.strip()}")
                    break
            except:
                continue
        
        if not python_cmd:
            print("Python 3.10 not found. Please install it from:")
            print("https://www.python.org/downloads/release/python-31011/")
            input("Press Enter to exit...")
            return 1
        
        # Create virtual environment
        venv_dir = "venv_py310"
        print(f"\nCreating virtual environment in ./{venv_dir}")
        subprocess.run([python_cmd, "-m", "venv", venv_dir], check=True)
        
        # Determine activation script and pip path based on OS
        if platform.system() == "Windows":
            activate_script = os.path.join(venv_dir, "Scripts", "activate")
            pip_path = os.path.join(venv_dir, "Scripts", "pip")
        else:
            activate_script = os.path.join(venv_dir, "bin", "activate")
            pip_path = os.path.join(venv_dir, "bin", "pip")
        
        print("\nInstalling dependencies...")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip_path, "install", "-r", "requirements_py310.txt"], check=True)
        
        print("\n"+"="*80)
        print("Setup Complete!")
        print("="*80)
        print(f"To activate the virtual environment:")
        if platform.system() == "Windows":
            print(f"    {venv_dir}\\Scripts\\activate")
        else:
            print(f"    source {venv_dir}/bin/activate")
        print("\nTo build the desktop application:")
        print("    python build_desktop_app.py")
        print("\nTo run the desktop application directly:")
        print("    python desktop_app.py")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
