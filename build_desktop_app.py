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

def build_electron():
    print("[BUILD] Building Electron app...")
    # If you have a build step (e.g. React/Vue), run it here:
    if os.path.exists(os.path.join(ELECTRON_DIR, "package.json")):
        # Optionally: run npm run build if you have a build script
        try:
            with open(os.path.join(ELECTRON_DIR, "package.json")) as f:
                if '"build"' in f.read():
                    run("npm run build", cwd=ELECTRON_DIR, check=False)
        except Exception:
            pass
    # Build with electron-builder
    # Note: --compression and --icon are not valid CLI args; set them in electron-builder config/package.json
    builder_cmd = f"npx electron-builder --win --x64"
    run(builder_cmd, cwd=ELECTRON_DIR)

def main():
    print("\n===== AMRS Desktop App Build Script =====\n")
    ensure_venv()
    install_python_requirements()
    ensure_node_and_electron()
    build_electron()
    print("\n[BUILD] Build complete! Check the 'electron_app/dist' folder for your Windows installer or .exe file.\n")

if __name__ == "__main__":
    main()
