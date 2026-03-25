# -*- mode: python ; coding: utf-8 -*-
# Build from this folder:  .\build_exe.ps1  or  pyinstaller --clean --noconfirm fast_monitor.spec
import os

from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas_s, binaries_s, hiddenimports_s = collect_all("selenium")

spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.dirname(spec_dir)

a = Analysis(
    [os.path.join(spec_dir, "gui.py")],
    pathex=[project_root],
    binaries=binaries_s,
    datas=datas_s,
    hiddenimports=hiddenimports_s
    + [
        "fast_monitor",
        "fast_monitor.core",
        "fast_monitor.gui",
        "win10toast",
        "pkg_resources",
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
    name="FastMonitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    name="FastMonitor",
)
