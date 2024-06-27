# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['L:\\Departements\\BTDS_AD\\002_AFFS\\Lab Automation\\09. Tecan\\04. Tecan Custom GUI for .csv\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\DPerez36\\AppData\\Local\\Programs\\Python\\Python310\\Lib\\site-packages/customtkinter', 'customtkinter/')],
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
    [],
    exclude_binaries=True,
    name='app',
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app',
)
