# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the Windows desktop build (onedir).
# Build from the repo root:  pyinstaller DrosophilaActivityGUI.spec --noconfirm
from PyInstaller.utils.hooks import collect_all, copy_metadata

datas = [
    ("app.py", "."),
    ("make_sample_data.py", "."),
    ("dam", "dam"),
]
binaries = []
hiddenimports = []

# app.py / dam import these at runtime; run_app.py does not, so pull them in
# explicitly (data files, submodules, and dynamic libs).
for pkg in ("streamlit", "altair", "pyarrow", "pandas", "numpy",
            "matplotlib", "openpyxl"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Streamlit reads its own version via importlib.metadata at import time.
datas += copy_metadata("streamlit")

a = Analysis(
    ["run_app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DrosophilaActivityGUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DrosophilaActivityGUI",
)
