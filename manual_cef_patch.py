"""
Manual patch for CEF Python to make it work with Python 3.10
This script will guide you through manually editing the cefpython3 __init__.py file
"""
import importlib.util
import os
import subprocess
import sys

def find_module_path(module_name):
    """Find the path to a module without importing it"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return None
        return spec.origin
    except ImportError:
        return None

def open_in_editor(file_path):
    """Try to open a file in the default editor"""
    try:
        # Try to use the system's default program to open the file
        if sys.platform == 'win32':
            os.startfile(file_path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.call(['open', file_path])
        else:  # Linux and other Unix-like
            subprocess.call(['xdg-open', file_path])
        return True
    except Exception as e:
        print(f"Error opening file: {e}")
        return False

def main():
    """Guide the user through manual patching"""
    print("=" * 70)
    print("CEF Python Manual Patch Guide")
    print("=" * 70)
    
    # Find cefpython3 module
    cef_init_path = find_module_path("cefpython3")
    
    if not cef_init_path:
        print("Could not find cefpython3 module. Is it installed?")
        return False
    
    print(f"Found cefpython3 at: {cef_init_path}")
    print("\nManual patching instructions:")
    print("1. We'll now open the cefpython3 __init__.py file in your default editor")
    print("2. Look for code that checks Python version and raises an exception")
    print("3. The code will look similar to this:")
    print("   if sys.version_info[0] != X or sys.version_info[1] not in [Y, Z]:")
    print("       raise Exception(\"Python version not supported: \" + sys.version)")
    print("4. Comment out this code block or replace it with 'pass'")
    print("5. Save the file and close the editor")
    
    input("\nPress Enter to open the file in your editor...")
    
    if open_in_editor(cef_init_path):
        print("\nThe file should now be open in your editor.")
        input("After making the changes, press Enter to continue...")
        
        print("\nTesting the patched module...")
        try:
            import cefpython3
            print("✓ Success! The patched cefpython3 module imported without errors.")
            print("\nYou can now try running your build script again.")
            return True
        except Exception as e:
            print(f"✗ Error importing cefpython3: {e}")
            print("The patch may not have been applied correctly.")
            return False
    else:
        print("\nCould not open the file automatically.")
        print(f"Please manually open and edit: {cef_init_path}")
        print("Follow the patching instructions above.")
        return False

if __name__ == "__main__":
    main()
