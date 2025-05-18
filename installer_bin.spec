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
    continue_yn: str = input('Are you sure you wish to include no files (y/n/yes/no): ').strip().lower()
    if not continue_yn in ('y', 'yes'):
        exit()


app_name: str = input('Enter the app name (default: install_from_web): ') or 'install_from_web'


a = Analysis(
    ['install_from_web.py'],
    pathex=[],
    binaries=[],
    datas=json_files,
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
    a.binaries,
    a.datas,
    [],
    name=app_name,
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
