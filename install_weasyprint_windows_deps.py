import os
import zipfile
import urllib.request
import shutil

# The official WeasyPrint dependencies URL is returning 404
# Using an alternative source for the DLLs
WEASYPRINT_DEPS_URL = "https://github.com/Kozea/WeasyPrint/files/10923047/weasyprint_dependencies.zip"

# Path to your packaged venv Scripts directory (adjust if needed)
VENV_SCRIPTS = os.path.join(os.path.dirname(__file__), 'dist', 'win-unpacked', 'resources', 'venv', 'Scripts')

# Download location for the zip file
deps_zip = os.path.join(os.path.dirname(__file__), 'weasyprint_dependencies.zip')

print(f"[WeasyPrint DLL Installer] Downloading dependencies from {WEASYPRINT_DEPS_URL} ...")
try:
    urllib.request.urlretrieve(WEASYPRINT_DEPS_URL, deps_zip)
    print(f"[WeasyPrint DLL Installer] Download successful.")
except Exception as e:
    print(f"[WeasyPrint DLL Installer] Download failed: {e}")
    # If this fails, try the alternative URL
    try:
        alt_url = "https://github.com/GTKfonts/GTKfonts/raw/main/weasyprint_dependencies.zip"
        print(f"[WeasyPrint DLL Installer] Trying alternative URL: {alt_url}")
        urllib.request.urlretrieve(alt_url, deps_zip)
        print(f"[WeasyPrint DLL Installer] Alternative download successful.")
    except Exception as e2:
        print(f"[WeasyPrint DLL Installer] All download attempts failed. Please manually download and install the WeasyPrint DLLs.")
        raise e2

print(f"[WeasyPrint DLL Installer] Extracting DLLs ...")
try:
    # Create the Scripts directory if it doesn't exist
    os.makedirs(VENV_SCRIPTS, exist_ok=True)
    
    with zipfile.ZipFile(deps_zip, 'r') as zip_ref:
        zip_ref.extractall(VENV_SCRIPTS)
    
    print(f"[WeasyPrint DLL Installer] DLLs extracted to {VENV_SCRIPTS}")
    os.remove(deps_zip)
    
    # Optionally, print the DLLs now present
    print("[WeasyPrint DLL Installer] DLLs in Scripts directory:")
    for f in os.listdir(VENV_SCRIPTS):
        if f.lower().endswith('.dll'):
            print(" -", f)
except Exception as e:
    print(f"[WeasyPrint DLL Installer] Extraction failed: {e}")
    raise
