"""
Patch script for CEF Python to enable compatibility with Python 3.10
WARNING: This is a compatibility hack that overrides version checking.
"""
import os
import sys
import re
import shutil
import importlib.util
from pathlib import Path

def find_cefpython_init():
    """Find the cefpython3 __init__.py file"""
    try:
        # Try to find the module without importing it
        spec = importlib.util.find_spec("cefpython3")
        if not spec or not spec.origin:
            print("Could not find cefpython3 module")
            return None
        
        init_path = spec.origin
        print(f"Found cefpython3 __init__.py at: {init_path}")
        return init_path
    except ImportError:
        print("cefpython3 is not installed")
        return None

def backup_file(file_path):
    """Create a backup of the file if one doesn't exist"""
    backup_path = f"{file_path}.bak"
    if not os.path.exists(backup_path):
        print(f"Creating backup at {backup_path}")
        shutil.copy2(file_path, backup_path)
    return backup_path

def patch_file(file_path):
    """Patch the file to remove version checks"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find Python version check code
    version_check_pattern = r'if\s+sys\.version_info\[\d\]\s+!=\s+\d+\s+or.+?raise\s+Exception\("Python\s+version\s+not\s+supported.+?\)'
    
    # Check for multiline version (by using re.DOTALL)
    modified_content = re.sub(version_check_pattern, 
                              '# Version check disabled by patch_cefpython.py\n'
                              'if False:  # Original version check disabled\n'
                              '    pass',
                              content, 
                              flags=re.DOTALL)
    
    # If the pattern wasn't found, try some alternative approaches
    if modified_content == content:
        # Try to find a simpler pattern - just the exception raising
        raise_pattern = r'raise\s+Exception\("Python\s+version\s+not\s+supported.+?\)'
        modified_content = re.sub(raise_pattern, 
                                '# Exception disabled by patch_cefpython.py\n'
                                'pass  # Original version check disabled',
                                content, 
                                flags=re.DOTALL)
    
    # If still no change, try manual patching with line numbers
    if modified_content == content:
        print("Pattern matching failed, attempting manual patching...")
        lines = content.split('\n')
        for i in range(len(lines)):
            if "Python version not supported" in lines[i]:
                # Found the exception line, now find the if statement before it
                for j in range(i, max(0, i-20), -1):
                    if lines[j].strip().startswith('if ') and 'sys.version_info' in lines[j]:
                        # Found the if statement that starts the version check
                        lines[j] = '# if statement disabled by patch\nif False:  # ' + lines[j]
                        modified_content = '\n'.join(lines)
                        break
                break
    
    if modified_content != content:
        with open(file_path, 'w') as f:
            f.write(modified_content)
        print(f"Successfully patched {file_path}")
        return True
    else:
        print("Could not patch file: No matching patterns found")
        return False

def patch_cefpython_module():
    """Main function to patch the cefpython3 module"""
    print("=" * 70)
    print("CEF Python Python 3.10 Compatibility Patch")
    print("=" * 70)
    
    # Find the cefpython3 __init__.py file
    init_path = find_cefpython_init()
    if not init_path:
        print("Failed to find cefpython3 module")
        return False
    
    # Backup the file
    backup_path = backup_file(init_path)
    print(f"Backup created at {backup_path}")
    
    # Patch the file
    if patch_file(init_path):
        print("\nPatch applied successfully!")
        print("\nNOTE: This is a compatibility hack and may cause issues.")
        print("If you encounter problems, restore the original file from the backup.")
        return True
    else:
        print("\nPatch failed!")
        print("Try manually editing the file to remove Python version checks.")
        return False

if __name__ == "__main__":
    if patch_cefpython_module():
        sys.exit(0)
    else:
        sys.exit(1)
