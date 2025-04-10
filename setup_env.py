"""
Setup script to create a Python virtual environment for AMRS Maintenance Tracker
"""
import os
import sys
import subprocess
import platform

def main():
    print("="*80)
    print("AMRS Maintenance Tracker - Environment Setup")
    print("="*80)
    
    # Determine Python version
    python_version = platform.python_version()
    print(f"Using Python {python_version}")
    
    # Create virtual environment directory
    venv_dir = "venv"
    print(f"\nCreating virtual environment in {venv_dir}...")
    
    try:
        # Use the built-in venv module instead of virtualenv
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        print("✓ Virtual environment created successfully")
        
        # Determine activation script path based on OS
        if platform.system() == "Windows":
            activate_script = os.path.join(venv_dir, "Scripts", "activate")
            pip_path = os.path.join(venv_dir, "Scripts", "pip")
        else:
            activate_script = os.path.join(venv_dir, "bin", "activate")
            pip_path = os.path.join(venv_dir, "bin", "pip")
        
        # Install required dependencies
        print("\nInstalling dependencies...")
        
        # Create requirements file if it doesn't exist
        if not os.path.exists("requirements.txt"):
            with open("requirements.txt", "w") as f:
                f.write("""# Core dependencies
flask==2.2.5
flask_sqlalchemy==3.0.5
flask_login==0.6.2
werkzeug==2.2.3
SQLAlchemy==2.0.21
Jinja2==3.1.2

# Desktop application
cefpython3==66.1
requests==2.28.2

# Build tools
pyinstaller==6.0.0
""")
        
        # Upgrade pip first
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        
        # Install dependencies from requirements.txt
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("✓ Dependencies installed successfully")
        
        print("\n"+"="*80)
        print("Setup Complete!")
        print("="*80)
        print(f"\nTo activate the virtual environment:")
        if platform.system() == "Windows":
            print(f"    {venv_dir}\\Scripts\\activate")
        else:
            print(f"    source {venv_dir}/bin/activate")
        
        print("\nAfter activation, you can run:")
        print("    python desktop_app.py")
        
        return 0
    except Exception as e:
        print(f"\nError: {e}")
        print("\nAlternative setup method:")
        print("1. Install venv manually: python -m pip install virtualenv")
        print("2. Create environment:    python -m venv venv")
        print("3. Activate environment:  venv\\Scripts\\activate (Windows)")
        print("                         source venv/bin/activate (Linux/Mac)")
        print("4. Install dependencies:  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
