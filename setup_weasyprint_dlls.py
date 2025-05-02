import os
import shutil
import sys

# Create dependencies directory
deps_dir = os.path.join(os.path.dirname(__file__), 'dependencies', 'weasyprint-dlls')
os.makedirs(deps_dir, exist_ok=True)

print(f"[DLL Setup] Local dependencies directory created at: {deps_dir}")
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