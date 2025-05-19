# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


def validate_path(file_path: str) -> bool:
    """
    Validate the string path
    :param file_path: String representation of a path
    """
    base_dir: Path = Path(SPEC).parent
    root_path: Path = Path(file_path)
    relative_path: Path = base_dir.joinpath(file_path)

    return any((root_path.is_file(), relative_path.is_file()))


# Get json files to include
json_files: list = []
print('Enter the JSON file paths you want to include (one per line).')
print(f'Use full paths for relative from {Path(SPEC).parent}.')
print('Type "exit" or just press Enter to finish.')

while True:
    json_file: str = input('Enter a JSON file path: ').strip()

    if json_file.lower() == 'exit' or not json_file:
        break

    if json_file.endswith('.json') and validate_path(json_file):
        json_files.append((json_file, './'))
    else:
        print('Invalid entry. Only valid .json files are accepted. Check your path.')

# Print json files to include
print('JSON files to be included:')
for json_file in json_files:
    print(f' - {json_file[0]}')

# Check if the user wants to include no json files
if len(json_files) == 0:
    continue_yn: str = input('Are you sure you wish to include no files (y/n/yes/no)(default: y): ').strip().lower()
    if not continue_yn in ('y', 'yes', ''):
        exit()

# Icon to use
while True:
    user_icon: str = input('Enter the path for your app icon (default: resources/cmd.icns): ') or 'resources/cmd.icns'
    if validate_path(user_icon):
        print(user_icon)
        break
    else:
        print(f'{user_icon} is not a valid path')

app_name: str = input('Enter the app name (default: Installer): ') or 'Installer'
bundle_id: str = input('Enter the app bundle identifier (default: com.thedzy.installer): ') or 'com.thedzy.installer'
bundle_version: str = input('Enter the app bundle version (default: 1.0.0): ') or '1.0.0'

a = Analysis(
    ['install_from_web.py'],
    pathex=[],
    binaries=[],
    datas=json_files,
    hiddenimports=[],
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
    name=app_name,
)
app = BUNDLE(
    coll,
    name=f'{app_name}.app',
    icon=user_icon,
    bundle_identifier=bundle_id,
    version=bundle_version,
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleName': app_name,
                'CFBundleDisplayName': app_name,
                'CFBundleTypeIconFile': 'cmd.icns',
                'LSHandlerRank': 'Owner'
            }
        ]
    },
)
