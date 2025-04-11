# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# Explicitly copy app.py to the root of the distribution
added_files = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('app.py', '.'),
]

# Include models.py if it exists
if os.path.exists('models.py'):
    added_files.append(('models.py', '.'))

# Copy any database files if they exist
for db_file in Path('.').glob('*.db'):
    added_files.append((str(db_file), '.'))

a = Analysis(
    ['desktop_app.py'],
    pathex=[r'C:\Users\Dominic\Documents\GitHub\AMRS-Preventative-Maintenance'],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'werkzeug',
        'jinja2',
        'sqlalchemy',
        'sqlite3',
        'email.mime.text',  # Required for flask-mail
        'cefpython3',
        'importlib',
        'importlib.util',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Print debug info about what's being included
print("\nIncluded data files:")
# Safe way to print data info without assuming structure
for item in a.datas:
    print(f"  {item}")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AMRSMaintenanceTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to True for debugging, change to False for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AMRSMaintenanceTracker',
)
