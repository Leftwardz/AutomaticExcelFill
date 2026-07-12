# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

resource_dirs: list[tuple[str, str]] = []
for folder_name in ('theme', 'img'):
    folder_path = root / folder_name
    if folder_path.is_dir():
        resource_dirs.append((str(folder_path), folder_name))

a = Analysis(
    ['main.py'],
    pathex=[str(root)],
    binaries=[],
    datas=resource_dirs,
    hiddenimports=[
        'openpyxl',
        'msoffcrypto',
        'msoffcrypto.format.ooxml',
        'watchdog.observers.inotify',
        'watchdog.observers.polling',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    [],
    exclude_binaries=True,
    name='AutomaticExcelFill',
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

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutomaticExcelFill',
)
