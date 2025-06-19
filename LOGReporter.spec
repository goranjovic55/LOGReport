# -*- mode: python ; coding: utf-8 -*-
# Simplified PyInstaller spec file

block_cipher = None

# Add path to avoid missing modules
import sys
import os
sys.path.append(os.path.abspath('src'))

a = Analysis(
    ['src/main.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[('src/nodes.json', 'src'), 
           ('assets', 'assets'),
           ('version_info.txt', '.')],
    hiddenimports=[
        'docx',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'reportlab',
        'PIL'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['src/runtime_hooks/runtime_hook.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='LOGReporter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    icon=None,
    version='version_info.txt',
)
