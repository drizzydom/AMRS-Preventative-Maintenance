import os
import shutil
import sys
import urllib.request
import zipfile
import tempfile

# Create dependencies directory
deps_dir = os.path.join(os.path.dirname(__file__), 'dependencies', 'weasyprint-dlls')
os.makedirs(deps_dir, exist_ok=True)

print(f"[DLL Setup] Local dependencies directory created at: {deps_dir}")

# Check if DLLs already exist
existing_dlls = [f for f in os.listdir(deps_dir) if f.lower().endswith('.dll')] if os.path.exists(deps_dir) else []

if existing_dlls:
    print(f"[DLL Setup] Found {len(existing_dlls)} existing DLL files:")
    for dll in existing_dlls:
        print(f"  - {dll}")
    print("\n[DLL Setup] Do you want to download and replace these files? (y/n)")
    response = input().strip().lower()
    if response != 'y':
        print("[DLL Setup] Keeping existing DLL files. Setup complete.")
        sys.exit(0)

# Attempt to download the latest WeasyPrint GTK dependencies automatically
print("[DLL Setup] Attempting to download GTK dependencies automatically...")

# URLs to try for WeasyPrint dependencies
urls = [
    "https://github.com/Kozea/WeasyPrint/releases/download/v60.2/weasyprint-64.zip",
    "https://github.com/Kozea/WeasyPrint/releases/download/v60.1/weasyprint-64.zip", 
    "https://github.com/Kozea/WeasyPrint/releases/download/v60.0/weasyprint-64.zip",
    "https://github.com/Kozea/WeasyPrint/releases/download/v59.0/weasyprint-64.zip"
]

success = False
for url in urls:
    try:
        print(f"[DLL Setup] Trying to download from: {url}")
        # Create a temporary file for the zip
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            deps_zip = temp_file.name
        
        # Download the file
        urllib.request.urlretrieve(url, deps_zip)
        
        print(f"[DLL Setup] Download successful from {url}")
        
        # Extract the zip
        with zipfile.ZipFile(deps_zip, 'r') as zip_ref:
            # Extract to the dependencies directory
            print(f"[DLL Setup] Extracting DLLs to {deps_dir}")
            for file in zip_ref.namelist():
                if file.lower().endswith('.dll'):
                    source = zip_ref.open(file)
                    target = open(os.path.join(deps_dir, os.path.basename(file)), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                    print(f"  - Extracted {os.path.basename(file)}")
        
        # Clean up the zip file
        os.remove(deps_zip)
        success = True
        break
    except Exception as e:
        print(f"[DLL Setup] Error with {url}: {e}")

# Check what DLLs we have now
dll_files = [f for f in os.listdir(deps_dir) if f.lower().endswith('.dll')] if os.path.exists(deps_dir) else []

if success and dll_files:
    print(f"\n[DLL Setup] Successfully downloaded {len(dll_files)} DLL files:")
    for dll in dll_files:
        print(f"  - {dll}")
    print("\n[DLL Setup] DLLs are ready for use in the build process.")
else:
    print("\n[DLL Setup] Automatic download failed. Please download manually.")
    print("[DLL Setup] Please download WeasyPrint DLLs from one of these sources:")
    print("1. Latest WeasyPrint Windows zip: https://github.com/Kozea/WeasyPrint/releases/latest")
    print("2. Latest GTK+ Runtime: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/latest")
    print("\nExtract the DLLs to this folder:")
    print(os.path.abspath(deps_dir))
    print("\nRequired DLL files:")
    print("libcairo-2.dll, libffi-7.dll, libfontconfig-1.dll, libfreetype-6.dll")
    print("libgdk_pixbuf-2.0-0.dll, libglib-2.0-0.dll, libgobject-2.0-0.dll")
    print("libharfbuzz-0.dll, libiconv-2.dll, libintl-8.dll, libjpeg-8.dll")
    print("libpango-1.0-0.dll, libpangocairo-1.0-0.dll, libpangoft2-1.0-0.dll")
    print("libpng16-16.dll, librsvg-2-2.dll, libxml2-2.dll, zlib1.dll")
    print("\nAfter downloading and extracting the DLLs, future builds will use these local files.")