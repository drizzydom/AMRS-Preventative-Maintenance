import os
import zipfile
import urllib.request
import shutil

# URL for the latest WeasyPrint Windows dependencies
WEASYPRINT_DEPS_URL = "https://github.com/Kozea/WeasyPrint/releases/latest/download/weasyprint_dependencies.zip"

# Path to your packaged venv Scripts directory (adjust if needed)
VENV_SCRIPTS = os.path.join(os.path.dirname(__file__), 'dist', 'win-unpacked', 'resources', 'venv', 'Scripts')

# Download location for the zip file
deps_zip = os.path.join(os.path.dirname(__file__), 'weasyprint_dependencies.zip')

print(f"[WeasyPrint DLL Installer] Downloading dependencies from {WEASYPRINT_DEPS_URL} ...")
urllib.request.urlretrieve(WEASYPRINT_DEPS_URL, deps_zip)

print(f"[WeasyPrint DLL Installer] Extracting DLLs ...")
with zipfile.ZipFile(deps_zip, 'r') as zip_ref:
    zip_ref.extractall(VENV_SCRIPTS)

print(f"[WeasyPrint DLL Installer] DLLs extracted to {VENV_SCRIPTS}")
os.remove(deps_zip)

# Optionally, print the DLLs now present
print("[WeasyPrint DLL Installer] DLLs in Scripts directory:")
for f in os.listdir(VENV_SCRIPTS):
    if f.lower().endswith('.dll'):
        print(" -", f)
