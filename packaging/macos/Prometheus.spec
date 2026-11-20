# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import runpy
from PyInstaller.utils.hooks import collect_data_files

layout = runpy.run_path(str(Path(SPECPATH) / "layout.py"))
root = layout["ROOT"]
version = layout["VERSION"]
icon = layout["APP_ICON"]

a = Analysis(
    [str(root / "prometheus" / "__main__.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "prometheus" / "assets" / "pix_qr.jpg"), "prometheus/assets"),
        (str(icon), "icon/prometheus-icon-apple Exports"),
    ] + collect_data_files("docx", include_py_files=True),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
# Including binaries/data directly in EXE preserves the one-file requirement.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=layout["APP_NAME"],
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon),
)
app = BUNDLE(
    exe,
    name=layout["BUNDLE_NAME"],
    icon=str(icon),
    bundle_identifier=layout["BUNDLE_ID"],
    version=version,
    info_plist={
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version,
        "LSMinimumSystemVersion": layout["MINIMUM_MACOS"],
    },
)
