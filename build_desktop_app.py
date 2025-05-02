import os
import sys
import subprocess
import shutil
import platform
import venv
from pathlib import Path

# --- CONFIGURABLE ---
PYTHON_VERSION = "3.9"
VENV_DIR = "venv_py39_electron"
REQUIREMENTS = "requirements.txt"
ELECTRON_DIR = "electron_app"
ICON_PATH = os.path.join(ELECTRON_DIR, "icons", "app.ico")  # Use your custom icon if present
COMPRESS_WITH_UPX = False  # Set to True for maximum compression, False for fastest build
COMPRESSION_LEVEL = "store"  # Use 'store' for fastest, 'maximum' for smallest

# --- UTILS ---
def run(cmd, cwd=None, shell=True, check=True):
    print(f"[BUILD] Running: {cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=shell)
    if check and result.returncode != 0:
        print(f"[BUILD] Command failed: {cmd}")
        sys.exit(result.returncode)
    return result.returncode == 0

def find_python_39():
    candidates = [
        "python3.9", "python39", r"C:\\Python39\\python.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\\Programs\\Python\\Python39\\python.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\\Python39\\python.exe"),
    ]
    for exe in candidates:
        try:
            out = subprocess.check_output(f'"{exe}" --version', shell=True, text=True)
            if "3.9" in out:
                return exe
        except Exception:
            continue
    return None

def ensure_venv():
    venv_path = Path(VENV_DIR)
    if venv_path.exists() and (venv_path / "pyvenv.cfg").exists():
        print(f"[BUILD] Found existing venv: {VENV_DIR}")
        return True
    print(f"[BUILD] Creating venv: {VENV_DIR}")
    python = find_python_39()
    if not python:
        print("[ERROR] Python 3.9 not found. Please install Python 3.9.")
        sys.exit(1)
    run(f'"{python}" -m venv "{VENV_DIR}"')
    return True

def venv_python():
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "python3")

def venv_pip():
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "pip.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "pip3")

def install_python_requirements():
    pip = venv_pip()
    print("[BUILD] Installing Python requirements...")
    run(f'"{pip}" install --upgrade pip setuptools wheel')
    run(f'"{pip}" install -r "{REQUIREMENTS}"')

def check_node():
    try:
        subprocess.check_output("node --version", shell=True)
        subprocess.check_output("npm --version", shell=True)
        return True
    except Exception:
        return False

def check_electron_builder():
    try:
        subprocess.check_output("npx electron-builder --version", shell=True)
        return True
    except Exception:
        return False

def ensure_node_and_electron():
    if not check_node():
        print("[ERROR] Node.js and npm are required. Please install from https://nodejs.org/en/download/")
        sys.exit(1)
    if not os.path.exists(ELECTRON_DIR):
        print(f"[ERROR] Electron app directory '{ELECTRON_DIR}' not found.")
        sys.exit(1)
    # Install node modules
    print("[BUILD] Installing npm dependencies...")
    run("npm install", cwd=ELECTRON_DIR)
    # Install electron-builder if not present
    if not check_electron_builder():
        print("[BUILD] Installing electron-builder...")
        run("npm install --save-dev electron-builder", cwd=ELECTRON_DIR)

def bundle_encryption_key():
    """
    Run the script to bundle the encryption key from environment variables
    """
    try:
        print("[BUILD] Bundling encryption key for desktop app...")
        subprocess.check_call([
            sys.executable,
            os.path.join(os.path.dirname(__file__), 'bundle_encryption_key.py')
        ])
        print("[BUILD] Encryption key bundled successfully.")
    except Exception as e:
        print(f"[BUILD] Warning: Failed to bundle encryption key: {e}")
        print("[BUILD] The desktop app will generate a new key during installation.")
        print("[BUILD] Note: This means users won't be able to read data encrypted by the Render instance.")

def copy_flask_resources():
    """
    Ensure app.py, static/, and templates/ are copied to the packaged resources directory.
    """
    import shutil
    base_dir = os.path.dirname(__file__)
    dist_resources = os.path.join(base_dir, 'electron_app', 'dist', 'win-unpacked', 'resources')
    os.makedirs(dist_resources, exist_ok=True)
    # Copy app.py
    shutil.copy2(os.path.join(base_dir, 'app.py'), os.path.join(dist_resources, 'app.py'))
    # Copy static/
    static_src = os.path.join(base_dir, 'static')
    static_dst = os.path.join(dist_resources, 'static')
    if os.path.exists(static_dst):
        shutil.rmtree(static_dst)
    shutil.copytree(static_src, static_dst)
    # Copy templates/
    templates_src = os.path.join(base_dir, 'templates')
    templates_dst = os.path.join(dist_resources, 'templates')
    if os.path.exists(templates_dst):
        shutil.rmtree(templates_dst)
    shutil.copytree(templates_src, templates_dst)
    print("[BUILD] Copied app.py, static/, and templates/ to packaged resources.")

def main():
    print("\n===== AMRS Desktop App Build Script =====\n")
    ensure_venv()
    install_python_requirements()
    ensure_node_and_electron()
    
    # Bundle encryption key from environment
    bundle_encryption_key()
    
    # Build Electron app and package everything
    print("[BUILD] Building Electron app and packaging...")
    # If you have a build step (e.g. React/Vue), run it here:
    if os.path.exists(os.path.join(ELECTRON_DIR, "package.json")):
        try:
            with open(os.path.join(ELECTRON_DIR, "package.json")) as f:
                if '"build"' in f.read():
                    run("npm run build", cwd=ELECTRON_DIR, check=False)
        except Exception:
            pass
    # Build with electron-builder (now part of this script)
    builder_cmd = "npx electron-builder --win --x64"
    run(builder_cmd, cwd=ELECTRON_DIR)
    
    # After building the app, run the post-build script to ensure all files are copied
    try:
        print("[BUILD] Running post-build file copy to ensure all files are present...")
        subprocess.check_call([
            sys.executable,
            os.path.join(os.path.dirname(__file__), 'post_build_copy.py')
        ])
        print("[BUILD] Post-build file copy completed.")
    except Exception as e:
        print(f"[BUILD] Failed to run post-build file copy: {e}")
    
    # Ensure Flask resources are copied
    copy_flask_resources()
    
    # Install WeasyPrint executable (new approach)
    try:
        print("[BUILD] Installing WeasyPrint executable...")
        subprocess.check_call([
            sys.executable,
            os.path.join(os.path.dirname(__file__), 'install_weasyprint_exe.py')
        ])
        print("[BUILD] WeasyPrint executable installed.")
    except Exception as e:
        print(f"[BUILD] Failed to install WeasyPrint executable: {e}")
        # Fall back to the DLL approach if exe installation fails
        try:
            print("[BUILD] Falling back to WeasyPrint DLL installation...")
            subprocess.check_call([
                sys.executable,
                os.path.join(os.path.dirname(__file__), 'install_weasyprint_windows_deps.py')
            ])
            print("[BUILD] WeasyPrint DLLs installed.")
        except Exception as e2:
            print(f"[BUILD] Failed to install WeasyPrint DLLs: {e2}")
            print("[BUILD] PDF generation may not work in the packaged app.")
    
    # Also copy the encryption key to the final build location
    try:
        src_key_path = os.path.join(ELECTRON_DIR, "resources", ".env.key")
        if os.path.exists(src_key_path):
            dist_resources_path = os.path.join(ELECTRON_DIR, "dist", "win-unpacked", "resources")
            os.makedirs(dist_resources_path, exist_ok=True)
            shutil.copy2(src_key_path, os.path.join(dist_resources_path, ".env.key"))
            print("[BUILD] Copied encryption key to final build location.")
    except Exception as e:
        print(f"[BUILD] Warning: Failed to copy encryption key to build output: {e}")
    
    print("\n[BUILD] Build complete! Check the 'electron_app/dist' folder for your Windows installer or .exe file.\n")

if __name__ == "__main__":
    main()
