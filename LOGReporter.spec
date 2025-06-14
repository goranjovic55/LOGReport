# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[('C:\\Program Files\\Python311\\Lib\\site-packages\\PyQt6\\*', 'PyQt6'), ('C:\\Program Files\\Python311\\Lib\\site-packages\\PyQt6\\Qt6\\bin\\Qt6Core.dll', '.'), ('C:\\Program Files\\Python311\\Lib\\site-packages\\PyQt6\\Qt6\\bin\\Qt6Gui.dll', '.'), ('C:\\Program Files\\Python311\\Lib\\site-packages\\PyQt6\\Qt6\\bin\\Qt6Widgets.dll', '.')],
    datas=[('src', 'src'), ('_PROJECT', '_PROJECT'), ('test_logs', 'test_logs'), ('nodes.json', '.')],
    hiddenimports=['PyQt6.sip'],
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
    name='LOGReporter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
