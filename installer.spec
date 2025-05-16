# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['install_from_web.py'],
    pathex=[],
    binaries=[],
    datas=[('sample_configs/discord.json', './')],
    hiddenimports=['packaging'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Installer',
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
    icon=['resources/cmd.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Installer',
)
app = BUNDLE(
    coll,
    name='Installer.app',
    icon='resources/installer.app/Contents/Resources/cmd.icns',
    bundle_identifier='com.thedzy.installer',
    version='1.0.0',
     info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleName': 'Installer',
                'CFBundleDisplayName': 'Installer',
                'CFBundleTypeIconFile': 'cmd.icns',
                'LSHandlerRank': 'Owner'
                }
            ]
        },
)
