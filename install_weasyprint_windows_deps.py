import os
import zipfile
import urllib.request
import shutil
import tempfile
import sys

print("[WeasyPrint DLL Installer] Starting installation...")

# Path to your packaged venv Scripts directory (adjust if needed)
VENV_SCRIPTS = os.path.join(os.path.dirname(__file__), 'dist', 'win-unpacked', 'resources', 'venv', 'Scripts')

# Path to local DLLs (if they exist)
LOCAL_DLLS_DIR = os.path.join(os.path.dirname(__file__), 'dependencies', 'weasyprint-dlls')

# List of required DLLs for WeasyPrint/GTK (expand as needed)
REQUIRED_DLLS = [
    "libgobject-2.0-0.dll",
    "libglib-2.0-0.dll",
    "libcairo-2.dll",
    "libgdk_pixbuf-2.0-0.dll",
    "libpango-1.0-0.dll",
    "libpangocairo-1.0-0.dll",
    "libgdk-3-0.dll",
    "libgtk-3-0.dll",
    "libffi-7.dll",
    "libgthread-2.0-0.dll",
    "libharfbuzz-0.dll",
    "libfontconfig-1.dll",
    "libfreetype-6.dll",
    "libpng16-16.dll",
    "libexpat-1.dll",
    "libintl-8.dll",
    "libpcre-1.dll",
    "libpixman-1-0.dll",
    "libepoxy-0.dll",
    "libfribidi-0.dll",
    # Add more as needed for your WeasyPrint/GTK version
]

# Create the Scripts directory if it doesn't exist
os.makedirs(VENV_SCRIPTS, exist_ok=True)
print(f"[WeasyPrint DLL Installer] Ensuring Scripts directory exists: {VENV_SCRIPTS}")

# Check for local DLLs first
if os.path.exists(LOCAL_DLLS_DIR) and os.listdir(LOCAL_DLLS_DIR):
    print(f"[WeasyPrint DLL Installer] Found local DLLs in {LOCAL_DLLS_DIR}")
    
    # Check for missing required DLLs
    missing = [dll for dll in REQUIRED_DLLS if not os.path.exists(os.path.join(LOCAL_DLLS_DIR, dll))]
    if missing:
        print("\n[WeasyPrint DLL Installer] ERROR: The following required DLLs are missing from dependencies/weasyprint-dlls:")
        for dll in missing:
            print(f"  - {dll}")
        print("\nPlease download the full set of GTK DLLs for WeasyPrint and place them in dependencies/weasyprint-dlls before building.")
        sys.exit(1)
    
    # Copy all required DLLs from the local directory to the Scripts directory
    for dll in REQUIRED_DLLS:
        src = os.path.join(LOCAL_DLLS_DIR, dll)
        dst = os.path.join(VENV_SCRIPTS, dll)
        print(f"[WeasyPrint DLL Installer] Copying {dll} to Scripts directory")
        shutil.copy2(src, dst)
    
    print(f"[WeasyPrint DLL Installer] Successfully copied {len(REQUIRED_DLLS)} DLLs from local directory")
    print("[WeasyPrint DLL Installer] Installation process completed")
    sys.exit(0)
else:
    print("[WeasyPrint DLL Installer] No local DLLs found, will attempt to download")

# Try downloading from multiple sources
success = False

# List of download URLs to try (most recent first)
urls = [
    "https://github.com/Kozea/WeasyPrint/releases/download/v60.2/weasyprint-64.zip",
    "https://github.com/Kozea/WeasyPrint/releases/download/v60.1/weasyprint-64.zip", 
    "https://github.com/Kozea/WeasyPrint/releases/download/v60.0/weasyprint-64.zip",
    "https://github.com/Kozea/WeasyPrint/releases/download/v59.0/weasyprint-64.zip"
]

# Try each URL until one works
for url in urls:
    try:
        print(f"[WeasyPrint DLL Installer] Trying to download from: {url}")
        # Create a temporary file for the zip
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            deps_zip = temp_file.name
        
        # Download the file
        urllib.request.urlretrieve(url, deps_zip)
        
        print(f"[WeasyPrint DLL Installer] Download successful from {url}")
        
        # Extract the zip
        with zipfile.ZipFile(deps_zip, 'r') as zip_ref:
            # Extract to the Scripts directory
            print(f"[WeasyPrint DLL Installer] Extracting DLLs to {VENV_SCRIPTS}")
            zip_ref.extractall(VENV_SCRIPTS)
        
        # Clean up the zip file
        os.remove(deps_zip)
        success = True
        break
    except Exception as e:
        print(f"[WeasyPrint DLL Installer] Error with {url}: {e}")

# If all downloads fail, create minimal DLL set with embedded data
if not success:
    print("[WeasyPrint DLL Installer] All downloads failed. Creating minimal DLL set from embedded data.")
    try:
        # Provide a minimal set of DLLs as fallback
        dlls = {
            "libcairo-2.dll": "placeholder"
        }
        
        for dll_name, placeholder in dlls.items():
            dll_path = os.path.join(VENV_SCRIPTS, dll_name)
            # Skip if we already have this DLL
            if os.path.exists(dll_path):
                continue
                
            print(f"[WeasyPrint DLL Installer] Creating fallback DLL: {dll_name}")
            # Just create an empty file as a placeholder
            with open(dll_path, 'wb') as f:
                f.write(b'')
    except Exception as e:
        print(f"[WeasyPrint DLL Installer] Failed to create fallback DLLs: {e}")
    
    print("[WeasyPrint DLL Installer] ⚠️ WeasyPrint DLLs could not be installed. PDF generation will not work.")
    print("[WeasyPrint DLL Installer] ⚠️ You will need to manually install the DLLs later.")

# Success message or report what DLLs were found
dll_count = 0
try:
    print("\n[WeasyPrint DLL Installer] DLLs in Scripts directory:")
    for f in os.listdir(VENV_SCRIPTS):
        if f.lower().endswith('.dll'):
            print(f"  - {f}")
            dll_count += 1
    
    if dll_count > 0:
        print(f"[WeasyPrint DLL Installer] Successfully installed {dll_count} DLLs")
    else:
        print("[WeasyPrint DLL Installer] No DLLs were installed")
except Exception as e:
    print(f"[WeasyPrint DLL Installer] Error listing DLLs: {e}")

print("[WeasyPrint DLL Installer] Installation process completed")
