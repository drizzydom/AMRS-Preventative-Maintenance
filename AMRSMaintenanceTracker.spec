# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Dominic\\Documents\\GitHub\\AMRS-Preventative-Maintenance\\webview_app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Dominic\\Documents\\GitHub\\AMRS-Preventative-Maintenance\\templates', 'templates'), ('C:\\Users\\Dominic\\Documents\\GitHub\\AMRS-Preventative-Maintenance\\static', 'static'), ('C:\\Users\\Dominic\\Documents\\GitHub\\AMRS-Preventative-Maintenance\\app', 'app'), ('C:\\Users\\Dominic\\Documents\\GitHub\\AMRS-Preventative-Maintenance\\app_bootstrap.py', '.'), ('C:\\Users\\Dominic\\Documents\\GitHub\\AMRS-Preventative-Maintenance\\secret_config.py', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AMRSMaintenanceTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
