import os
import shutil
import sys

# Create bin directory for executables
bin_dir = os.path.join(os.path.dirname(__file__), 'dependencies', 'bin')
os.makedirs(bin_dir, exist_ok=True)

print(f"[WeasyPrint Setup] Local bin directory created at: {bin_dir}")
print("[WeasyPrint Setup] Please copy weasyprint.exe from the WeasyPrint 65.1 release to this folder:")
print(os.path.abspath(bin_dir))
print("\nAfter copying weasyprint.exe, future builds will use this executable instead of requiring DLLs.")