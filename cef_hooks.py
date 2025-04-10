"""
Custom PyInstaller hooks for CEF Python
This prevents the recursive analysis issues during build
"""
import os
import glob
import sys
from pathlib import Path
import PyInstaller.utils.hooks as hooks

def collect_cef_files():
    """Collect all necessary CEF Python files without deep analysis"""
    datas = []
    binaries = []
    hiddenimports = []
    
    try:
        import cefpython3
        cef_dir = os.path.dirname(cefpython3.__file__)
        print(f"CEF Python found at: {cef_dir}")
        
        # Add the CEF Python files to the data files
        for filename in glob.glob(os.path.join(cef_dir, "*.*")):
            # Skip some files that are not needed
            if os.path.basename(filename).startswith("_"):
                continue
                
            if filename.endswith(('.pyd', '.dll', '.so')):
                # Add binary files (DLLs, etc.)
                binaries.append((filename, os.path.dirname(filename.replace(cef_dir, "cefpython3"))))
            else:
                # Add data files
                datas.append((filename, os.path.dirname(filename.replace(cef_dir, "cefpython3"))))
        
        # Add CEF process files
        subprocess_dir = os.path.join(cef_dir, "subprocess")
        if os.path.exists(subprocess_dir):
            for filename in glob.glob(os.path.join(subprocess_dir, "*.*")):
                binaries.append((filename, os.path.dirname(filename.replace(cef_dir, "cefpython3"))))
        
        # Add CEF locales
        locales_dir = os.path.join(cef_dir, "locales")
        if os.path.exists(locales_dir):
            for filename in glob.glob(os.path.join(locales_dir, "*.*")):
                datas.append((filename, os.path.dirname(filename.replace(cef_dir, "cefpython3"))))
        
        # Manually specify imports to avoid deep analysis
        hiddenimports.extend([
            'base64',
            'copy',
            'codecs',
            'datetime',
            'inspect',
            'json',
            'os',
            'platform',
            'random',
            're',
            'sys',
            'time',
            'traceback',
            'types',
            'urllib.parse'
        ])
        
    except ImportError:
        print("CEF Python not found!")
    
    return datas, binaries, hiddenimports

# Export data that PyInstaller will use
cef_datas, cef_binaries, cef_imports = collect_cef_files()
