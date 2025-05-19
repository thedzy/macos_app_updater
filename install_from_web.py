#!/usr/bin/env python3

__author__ = 'thedzy'
__copyright__ = 'Copyright 2024, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'
__date__ = '2025-05-12'
__description__ = \
    """
    install_from_web.py: 
    Install applications directly from the web
    """

import argparse
import atexit
import json
import logging.config
import mimetypes
import os
import plistlib
import pprint
import re
import shutil
import ssl
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Optional, Any
from urllib.parse import urlparse
from xml.etree.ElementTree import ElementTree


class ColourFormat(logging.Formatter):
    """
    Add colour to logging events
    """

    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%', levels={}) -> None:
        """
        Initialise the formatter
        ft: (str) Format String
        datefmt: (str) Date format
        style: (str) Format style
        levels: tuple, tuple (level number start, colour, attribute
        """
        self.levels = {}
        set_levels: dict = {10: 90, 20: 92, 30: 93, 40: 91, 50: (41, 97)}
        set_levels.update(levels)

        for key in sorted(set_levels.keys()):
            value: int = set_levels[key]
            colour: str = str(value) if isinstance(value, (str, int)) else ';'.join(map(str, value))

            self.levels[key] = f'\x1b[5;{colour};m'

        super().__init__(fmt, datefmt, style)

    def formatMessage(self, record: logging.LogRecord, **kwargs: dict) -> str:
        """
        Override the formatMessage method to add colour
        """
        no_colour: str = u'\x1b[0m'
        for level in self.levels:
            colour: str = self.levels[level] if record.levelno >= level else colour

        return f'{colour}{super().formatMessage(record, **kwargs)}{no_colour}'


class CustomRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        super().__init__()
        self.final_url = None  # Store the final redirected URL
        self.last_url = None  # Store the last URL (for Referer)

    def redirect_request(self, req, fp, code, msg, headers, new_url):
        logger.warning(f'Redirecting to: {new_url}')
        self.final_url = new_url  # Update the final URL

        # Set the Referer header to the previous URL
        if self.last_url:
            req.add_header('Referer', self.last_url)
            logger.debug(f'Setting Referer: {self.last_url}')

        # Update last_url for next redirect
        self.last_url = req.full_url

        return super().redirect_request(req, fp, code, msg, headers, new_url)


def main():
    logger.info('Start')

    parsed_json_url: urlparse = urlparse(options.url)
    if not all([parsed_json_url.scheme, parsed_json_url.netloc]):
        logger.critical(f'url "{options.url}" does not appear to be valid')
        return 4

    # Check if we are blocking
    if options.blocking_app is not None:
        # Check if app is blocking
        blocked, line = is_app_running(options.blocking_app)
        if blocked:
            logger.warning(f'App "{options.blocking_app}" is believed to be running: {line}')
            return 0
    if options.blocking_file is not None:
        # Check if app is blocking
        blocking_file_path: Path = Path(options.blocking_file)
        if blocking_file_path.exists():
            blocking_file_type: str = 'file' if blocking_file_path.is_file() else 'directory'
            logger.warning(f'"{options.blocking_file}" is a {blocking_file_type} and the install/update will not run')
            return 0
    if options.required_file is not None:
        # Check if app is blocking
        required_file_path: Path = Path(options.required_file)
        if not required_file_path.exists():
            logger.warning(f'"{required_file_path}" is missing and the install/update will not run')
            return 0

    # Folder/files for saved contents
    temp_folder: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory()
    installer_file: str = get_filename(options.url)
    installer_path: Path = Path(temp_folder.name).joinpath(installer_file)
    unpack_path: Path = Path(temp_folder.name).joinpath('contents')
    unpack_path.mkdir(exist_ok=True)

    # Register cleanup at exit
    atexit.register(temp_folder.cleanup)

    # Setup ssl verification for downloads
    ssl_context: ssl.SSLContext = ssl.create_default_context()
    ssl_context.load_verify_locations(export_system_root_certs())
    ssl_context.load_default_certs()

    # Create an opener with redirect handling and SSL context
    redirect_handler: CustomRedirectHandler = CustomRedirectHandler()
    opener: urllib.request.OpenerDirector = urllib.request.build_opener(
        redirect_handler,
        urllib.request.HTTPSHandler(context=ssl_context)
    )
    opener.addheaders = [
        ('User-Agent', options.user_agent),
        ('Sec-Fetch-Site', 'none'),
        ('Sec-Fetch-Mode', 'navigate'),
        ('Sec-Fetch-Dest', 'document'),
        ('Sec-Fetch-User', '?1')
    ]  # Ensure headers are preserved

    # If regex of code get the html/text
    if any((options.regex, options.code)):
        try:
            # Create the request with custom User-Agent
            req: urllib.request.Request = urllib.request.Request(options.url)
            req.add_header('User-Agent', options.user_agent)

            # Fetch the page
            with opener.open(req) as response:
                html: str = response.read().decode()
        except Exception as err:
            logger.error(f'Error fetching page: {err}')
            return 5

    # Regex for the term
    if options.regex is not None:
        logger.info(f'Finding download in page "{options.url}" using: "{options.regex}" ...')

        # If regex is specified, use it to find the link
        try:
            matches: Optional[re.Match] = re.search(options.regex, html)

            # Find the link
            if matches:
                download_url: str = matches.group()
                logger.info(f'Found download URL: {download_url}')
            else:
                logger.error('No matching download URL found.')
                return 1

        except Exception as err:
            logger.error(f'Error fetching page: {err}')
            return 5

    # Pipe the html into the code
    elif options.code is not None:
        logger.info(f'Finding download in page "{options.url}" using: provided code ...')

        # Processes code
        try:
            # Run the user-provided code as a shell command, with HTML piped in
            process: subprocess.Popen = subprocess.Popen(
                options.code,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                executable='/bin/bash'  # Explicitly use bash for shell commands
            )

            # Send the HTML content to the command
            stdout, stderr = process.communicate(input=html)

            if process.returncode == 0:
                download_url: str = stdout.strip()
                logger.info(f'Found download URL: {download_url}')
            else:
                logger.critical(f'Command failed. Error: {stderr.strip()}')
                return 5

        except subprocess.CalledProcessError as err:
            logger.critical(f'Failed to run provided code. Error: {err.stderr.strip()}')
            return 5

    else:
        download_url: str = options.url

    # Ensure the URL has a full schema (http/https) and domain
    parsed_base: urllib.parse.ParseResult = urlparse(options.url)
    if not urlparse(download_url).scheme:
        if download_url.startswith('/'):
            # Absolute path (domain only)
            download_url: str = f'{parsed_base.scheme}://{parsed_base.netloc}{download_url}'
        else:
            # Relative path (current directory of base URL)
            download_url: str = f'{parsed_base.scheme}://{parsed_base.netloc}{parsed_base.path}/{download_url}'
        logger.info(f'Adjusted download URL: {download_url}')

    # Download the install/app
    parsed_json_url: urlparse = urlparse(download_url)
    if not all([parsed_json_url.scheme, parsed_json_url.netloc]):
        logger.critical(f'url "{download_url}" does not appear to be valid')
        return 4

    start_time: float = time.time()
    try:
        logger.info(f'Downloading {download_url} ...')
        installer_file: str = get_filename(download_url)
        installer_path: Path = Path(temp_folder.name).joinpath(installer_file)

        # Create a request for the file download
        req_download: urllib.request.Request = urllib.request.Request(download_url)
        req_download.add_header('User-Agent', options.user_agent)

        # Download the file
        with opener.open(req_download) as download_response:
            # Get  file name from redirect if no extension from the link
            if Path(installer_file).suffix is None or Path(installer_file).suffix == '':
                download_url: str = redirect_handler.final_url if redirect_handler.final_url else download_url
                installer_file: str = get_filename(download_url)
                installer_path: Path = Path(temp_folder.name).joinpath(installer_file)

            # Save download
            with open(installer_path, 'wb') as file:
                file.write(download_response.read())
                logger.info(f'Saved to {installer_file}')
                logger.debug(f'Saved to {installer_path}')

    except Exception as err:
        logger.critical(err)
        return 5
    finally:
        # Get the time to download (or fail)
        end_time: float = time.time()
        minutes, seconds = divmod((end_time - start_time), 60)
        hours, minutes = divmod(minutes, 60)
        logger.info(f'Run time: {hours:02.0f}:{minutes:02.0f}:{seconds:04.1f}')

    # Get file type
    if options.file_type is not None:
        file_type: Optional[str] = options.file_type
        logger.info(f'Using provided file type: {file_type}')
    else:
        logger.info('Getting file type from mime types')
        mime_type, _ = mimetypes.guess_type(installer_file)

        if not mime_type:
            file_type: Optional[str] = None
        elif 'x-apple-diskimage' in mime_type:
            file_type: Optional[str] = 'dmg'
        elif 'x-tar' in mime_type:
            file_type: Optional[str] = 'tar.gz'
        elif 'x-xar' in mime_type:
            file_type: Optional[str] = 'pkg'
        elif 'zip' in mime_type:
            file_type: Optional[str] = 'zip'
        else:
            logger.warning(f'Unknown file type: {mime_type}')
            file_type: Optional[str] = None

    if file_type is None:
        # Detect from signatures
        logger.info('Getting file type from signature')
        file_type: Optional[str] = detect_mime_type(installer_path)

    if file_type is None and '.' in installer_file:
        # Essentially the same as mimetype, but last ditch
        file_type: Optional[str] = installer_file.split('.')[-1]

    if file_type is None:
        logger.critical(
            'Unable to get file type from options, mime or extension, use -t, --dmg, --pkg, --tar, or --zip')
        return 7

    logger.info(f'File type is: {file_type}')

    # Unpack
    if file_type.startswith('tar') or file_type.startswith('gz'):
        try:
            logger.info(f'Unpacking TAR {installer_path.stem} ...')
            with tarfile.open(installer_path, 'r') as tar:
                tar.extractall(path=unpack_path)
            logger.info(f'TAR unpacked to {unpack_path}')
        except tarfile.ReadError as err:
            logger.critical(err)
            return 8

    elif file_type == 'zip':
        try:
            logger.info(f'Unpacking ZIP {installer_path.stem} ...')
            with zipfile.ZipFile(installer_path, 'r') as zip_ref:
                for zip_info in zip_ref.infolist():
                    extracted_path: Path = Path(unpack_path, zip_info.filename)

                    # Detect if this should be a symlink
                    if zip_info.external_attr >> 28 == 0xA:  # Symlink in POSIX (0xA)
                        symlink_target: str = zip_ref.read(zip_info.filename).decode()
                        logger.debug(f'Creating symlink {extracted_path} -> {symlink_target}')
                        extracted_path.parent.mkdir(parents=True, exist_ok=True)
                        os.symlink(symlink_target, extracted_path)
                    else:
                        zip_ref.extract(zip_info, unpack_path)
                        # Apply permissions if this is an executable
                        perm: int = zip_info.external_attr >> 16
                        if perm:
                            logger.debug(f'Setting permissions for {extracted_path}: {oct(perm)}')
                            os.chmod(extracted_path, perm)
            logger.info(f'ZIP unpacked to {unpack_path}')
        except zipfile.BadZipFile as err:
            logger.critical(f'Error extracting ZIP: {err}')
            return 8

    elif file_type == 'dmg':
        mount_dmg(installer_path, unpack_path)

    elif file_type == 'pkg':
        install_pkg(installer_path, unpack_path)
        return 0

    # Get the installer/app
    app_path: Path = find_app_path(unpack_path)
    pkg_path: Path = find_app_path(unpack_path, '*.pkg', False)
    if app_path is not None:
        install_path: Path = options.app_install_path
        logger.info(f'Copying /{app_path.name} to {install_path}')

        # Get versions
        old_version: str = get_app_version(install_path.joinpath(app_path.name))
        new_version: str = get_app_version(app_path)
        logger.info(f'Current version installed {old_version}')
        logger.info(f'New version to install {new_version}')

        # Compare versions
        install: bool = options.reinstall
        if not old_version:
            logger.info('No current installation')
            install: bool = True
        elif not new_version:
            logger.error('Cannot get the new app version')
        elif version_parse(new_version) > version_parse(old_version):
            logger.info(f'Version to install {new_version} is newer than installed {old_version}.')
            install: bool = True
        elif version_parse(new_version) < version_parse(old_version):
            logger.info(f'Version to install {new_version} is older than installed {old_version}.')
            if options.allow_downgrade:
                install: bool = True
        else:
            logger.info('Both versions are identical.')

        # Install app
        if install:
            logger.info('Installing!')
            install_app(app_path, install_path)

    elif pkg_path is not None:
        logger.info(f'Installing {pkg_path} to {options.pkg_install_path}')
        install_pkg(pkg_path, unpack_path)
    else:
        logger.critical('No app or pkg found in installer')
        return 2

    logger.info('Done')
    return 0


def is_app_running(app_name: str) -> (bool, str):
    """
    Checks if the specified app is currently running.
    :param app_name: Name of the app (e.g., 'Terminal')
    :return: True if the app is running, False otherwise
    """
    try:
        # Run the 'ps aux' command to list all running processes
        result: subprocess.CompletedProcess = subprocess.run(['ps', '-axo', 'pid comm'], capture_output=True, text=True)

        # Check if any line contains the app name
        for line in result.stdout.splitlines():
            if options.blocking_app_insensitive:
                app_name: str = app_name.lower()
                line: str = line.lower()
            if app_name in line:
                return True, line

        return False, None

    except subprocess.CalledProcessError:
        return False, None


def get_filename(url: str) -> str:
    """
    Extracts the filename from the given URL.
    :param url: The URL string from which to extract the filename.
    :return: The filename (last part of the URL path).

    Example:
        >>> get_filename('http://somewhere.com/path/to/file/installer?type=macos.15&installer=universal')
        'installer'
    """
    # Parse the URL
    parsed_url: urllib.parse.ParseResult = urlparse(url.rstrip('/'))

    # Extract the last part of the path (filename)
    installer_file: str = parsed_url.path.split('/')[-1]
    return installer_file


def detect_mime_type(file_path: str) -> str:
    """
    Detects the MIME type of file using its magic number (file signature).
    :param file_path: The path to the file to detect.
    :return: The detected MIME type as a string
    """
    try:
        with open(file_path, 'rb') as file:
            header: bytes = file.read(16)

            # Detect file type by signature
            if header[0] == 0x50 and header[1] == 0x4B:  # ZIP file
                if header[2] in (0x03, 0x05, 0x07) and header[3] in (0x04, 0x06, 0x09):
                    return 'zip'

            if header.startswith(b'\x78\x61\x72\x21') or header.startswith(b'\x78\x9C'):  # XAR (pkg)
                return 'pkg'

            # Detect DMG (Zlib Compressed)
            if header[0] == 0x78:
                if header[1] in (0x01, 0x5E, 0x9C, 0xDA, 0x20, 0x7D, 0xBB, 0xF9):
                    return 'dmg'

            # Detect DMG (xy)
            if header[0:6] == b'\xFD\x37\x7A\x58\x5A\x00':
                return 'dmg'

            # Detect DMG (Apple Disk Image)
            if header[0:4] == b'plist' or header[0:4] == b'\x62\x70\x6C\x69':
                return 'dmg'

            # Detect Tar (z, gzip)
            if header[0] == 0x1F:
                if header[1] in (0x8B, 0x90, 0xA0):
                    return 'tar'
            if header.startswith(b'\x42\x5A\x68'):  # BZip2 (BZh)
                return 'tar'
            if header.startswith(b'\x75\x73\x74\x61\x72'):  # Tar (ustar)
                return 'tar'

        logger.debug(f'Unknown file type. Header: {header.hex().upper()}')
        return None

    except IndexError as err:
        logger.error(f'Empty File')
        return None
    except Exception as err:
        logger.error(f'Error detecting file type: {err}')
        return None


def mount_dmg(dmg_path: Path, mount_point: Path):
    """
    Mounts a DMG file using hdiutil (macOS only).
    :param dmg_path: Path to the DMG file.
    :param mount_point: Path where the DMG should be mounted.
    """
    try:
        logger.info(f'Mounting DMG {dmg_path} at {mount_point}')
        cmd: list[str] = [
            '/usr/bin/hdiutil', 'attach', '-nobrowse',
            '-mountpoint', mount_point.as_posix(),
            dmg_path.as_posix()
        ]
        logger.debug(' '.join(cmd))

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f'DMG mounted at {mount_point}')

        # Register unmount at exit
        atexit.register(lambda: unmount_dmg(mount_point))

    except subprocess.CalledProcessError as err:
        logger.critical(f'Failed to mount DMG. Error: {err.stderr.strip()}')
        return 5


def unmount_dmg(mount_point: Path):
    """
    Unmounts the DMG if it was mounted
    :param mount_point: The path to mount point of the dmg
    """
    if mount_point and mount_point.exists():
        logger.info(f'Unmounting DMG at {mount_point}')
        cmd: list[str] = ['/usr/bin/hdiutil', 'detach', mount_point.as_posix()]
        logger.debug(' '.join(cmd))
        subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info('DMG unmounted')


def find_app_path(install_files: Path, pattern: str = '*.app', directory: bool = True) -> Path:
    """
    Finds the first .app/pkg/other within the specified install_files directory.
    :param pattern: File/Directory pattern
    :param install_files: Path to the directory to search in
    :param directory: Is the file a directory
    :return: Path to the .app directory if found, None otherwise
    """
    logger.info(f'Searching for {pattern} directory in {install_files} ...')

    app: Optional[Path] = next(
        (path for path in install_files.rglob(pattern) if path.is_dir() == directory),
        None
    )

    if app:
        app_path: Path = Path(app)
        logger.info(f'Found {app_path.name}')
    else:
        return None

    return app_path


def get_app_version(app_path: Path) -> str:
    """
    Reads the CFBundleShortVersionString from the Info.plist file in a .app bundle.
    :param app_path: Path to the .app directory
    :return: The app version as a string, or None if not found
    """
    plist_path: str = app_path / 'Contents' / 'Info.plist'
    if not plist_path.exists():
        logger.error(f'Info.plist not found in {app_path}')
        return None

    try:
        with plist_path.open('rb') as plist_file:
            plist_data: Any = plistlib.load(plist_file)
            version: Any = plist_data.get('CFBundleShortVersionString')
            return version
    except Exception as e:
        logger.error(f'Error reading plist: {e}')
        return None


def install_app(app_path: Path, install_path: Path):
    """
    Copies the .app directory to the install path.
    :param app_path: Path to the .app directory to be installed
    :param install_path: Path where the .app should be installed
    """
    logger.info(f'Copying {app_path.name} to {install_path}')
    destination = install_path / app_path.name

    try:
        logger.debug(f'Using copy method: {options.copy_method}')

        if options.copy_method == 'shutil':

            if destination.exists():
                logger.info(f'Removing existing installation at {destination}')
                shutil.rmtree(destination)

            shutil.copytree(app_path, destination, copy_function=shutil.copy2, dirs_exist_ok=True)

        elif options.copy_method == 'cp':
            if destination.exists():
                logger.info(f'Removing existing installation at {destination}')
                shutil.rmtree(destination)

            cmd: list = [
                'cp', '-rp',
                app_path.as_posix(),
                destination.as_posix()
            ]
            logger.debug(' '.join(cmd))

            result: subprocess.CompletedProcesss = subprocess.run(cmd, text=True, stderr=subprocess.PIPE,
                                                                  stdout=subprocess.PIPE)
            logger.debug(result)

        elif options.copy_method == 'rsync':
            cmd: list = [
                'rsync', '-DgloprtLdEHW', '--delete',
                f'{app_path.as_posix()}/',
                destination.as_posix()
            ]
            logger.debug(' '.join(cmd))

            result: subprocess.CompletedProcess = subprocess.run(cmd, text=True, stderr=subprocess.PIPE,
                                                                 stdout=subprocess.PIPE)
            logger.debug(result)

        else:  # ditto
            if destination.exists():
                logger.info(f'Removing existing installation at {destination}')
                shutil.rmtree(destination)

            cmd: list = [
                'ditto',
                app_path.as_posix(),
                destination.as_posix()
            ]
            logger.debug(' '.join(cmd))

            result: subprocess.CompletedProcess = subprocess.run(cmd, text=True, stderr=subprocess.PIPE,
                                                                 stdout=subprocess.PIPE)
            logger.debug(result)
        logger.info('Installation complete.')
    except Exception as err:
        logger.error(f'Installation failed: {err}')

    if options.run:
        result: subprocess.CompletedProcess = subprocess.run(
            ['xattr', '-dr', 'com.apple.quarantine', destination.as_posix()],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            logger.info(f'Cleared quarantine attribute for {destination}')
        else:
            logger.warning(f'Failed to clear quarantine: {result.stderr}')

        result: subprocess.CompletedProcess = subprocess.run(['open', destination.as_posix()], check=True)

        if result.returncode == 0:
            logger.info(f'Launched {destination}')
        else:
            logger.error(f'Failed to launch {destination}. Error: {result.stderr}')


def install_pkg(pkg_path: Path, unpack_path: Path):
    """
    Installs the pkg to the installation path.
    :param pkg_path: Path to the .pkg to be installed
    :param unpack_path: Path to the directory to be unpacked
    """
    logger.info(f'Unpacking PKG {pkg_path.name} ...')
    pkg_extract_path: Path = unpack_path.parent.joinpath('pkg_extract')

    # Add pkg just in case its not there, installer will only install with a pkg extension
    if pkg_path.suffix != '.pkg':
        logger.info('Adding pkg extension for installer compatibility')
        pkg_path: Path = pkg_path.with_suffix('.pkg')

    # Extract
    cmd: list = ['/usr/sbin/pkgutil', '--expand', pkg_path.as_posix(), pkg_extract_path.as_posix()]
    logger.debug(' '.join(cmd))
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except subprocess.CalledProcessError as err:
        logger.critical(f'Failed to mount DMG. Error: {err.stderr.strip()}')
        return 5

    logger.debug(f'PKG unpacked to {pkg_extract_path}')

    # Check the version numbers against what is installed
    distribution_file = pkg_extract_path.joinpath('Distribution')
    package_info_file = pkg_extract_path.joinpath('PackageInfo')

    install: bool = options.reinstall
    if distribution_file.exists():
        logger.debug('Working from distribution pkg')
        try:
            # Parse the Distribution XML file
            tree: ElementTree = ET.parse(distribution_file)
            root = tree.getroot()

            # Iterate over all pkg-ref elements with a version attribute
            for pkg_ref in root.findall('.//pkg-ref[@version]'):
                package_id = pkg_ref.get('packageIdentifier') or pkg_ref.get('id')
                version: tuple = version_parse(pkg_ref.get('version'))

                if not package_id:
                    logger.warning('No package identifier found for this pkg-ref.')
                    continue

                logger.info(f'Checking package: {package_id} (Version: {version})')

                # Check installed version using pkgutil
                result: subprocess.CompletedProcess = subprocess.run(
                    ['/usr/sbin/pkgutil', '--pkg-info', package_id],
                    capture_output=True,
                    text=True,
                    check=False
                )

                installed_version: Optional[tuple] = None
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if line.startswith('version:'):
                            installed_version: Optional[tuple] = version_parse(line)  # line.split(':')[1].strip()
                            break

                # Compare versions
                if not installed_version:
                    logger.info(f'Package {package_id} is not installed.')
                    install: bool = True
                elif version == installed_version:
                    logger.info(f'Package {package_id} is already up to date (Version: {version}).')
                elif version > installed_version:
                    logger.info(
                        f'Package {package_id} has an update available: '
                        f'Installed {installed_version} → Available {version}'
                    )
                    install: bool = True
                elif version < installed_version:
                    logger.info(
                        f'Package {package_id} is a downgrade: '
                        f'Installed {installed_version} → Older {version}'
                    )
                    if options.allow_downgrade:
                        install: bool = True
        except ET.ParseError as e:
            logger.error(f'Failed to parse distribution file: {e}')
        except Exception as e:
            logger.error(f'Unexpected error: {e}')

    elif package_info_file.exists():
        logger.debug('Working from flat pkg')

        try:
            # Parse the PackageInfo XML file
            tree = ET.parse(package_info_file)
            root = tree.getroot()

            # Extract ID and Version from attributes
            package_id: str = root.attrib.get('identifier')
            version: str = root.attrib.get('version')

            logger.info(f'Checking package: {package_id} (Version: {version})')

            # Check installed version using pkgutil
            result: subprocess.CompletedProcess = subprocess.run(
                ['/usr/sbin/pkgutil', '--pkg-info', package_id],
                capture_output=True,
                text=True,
                check=False
            )

            installed_version = None
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith('version:'):
                        installed_version = line.split(':')[1].strip()
                        break

            # Compare versions
            if not installed_version:
                logger.info(f'Package {package_id} is not installed.')
                install = True
            elif version == installed_version:
                logger.info(f'Package {package_id} is already up to date (Version: {version}).')
            elif version > installed_version:
                logger.info(
                    f'Package {package_id} has an update available: '
                    f'Installed {installed_version} → Available {version}'
                )
                install = True
            elif version < installed_version:
                logger.info(
                    f'Package {package_id} is a downgrade: '
                    f'Installed {installed_version} → Older {version}'
                )
                if options.allow_downgrade:
                    install = True

        except ET.ParseError as e:
            logger.error(f'Failed to parse PackageInfo file: {e}')
        except Exception as e:
            logger.error(f'Unexpected error: {e}')

    if install:
        logger.info('Installing package...')

        try:
            cmd: list = ['sudo', '/usr/sbin/installer', '-pkg', pkg_path.as_posix(), '-target',
                         options.pkg_install_path.as_posix()]
            logger.debug(' '.join(cmd))
            result: subprocess.CompletedProcess = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info('Installation completed successfully.')
            else:
                logger.error(f'Installation failed with code {result.returncode}:\n{result.stderr}')

        except Exception as e:
            logger.error(f'Unexpected error during installation: {e}')


def version_parse(version_string: str) -> tuple:
    """
    Custom version parsing method that handles:
    - Numeric versions (1.2.3)
    - Build versions (Build 4192)
    - Pre-release versions (alpha, beta, rc)
    """
    # Strip leading text (like "Build " or "Version ")
    version_string = version_string.lstrip('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ- ')

    # Split the version by dots
    parts = version_string.split('.')

    # Convert numeric parts and handle alpha/beta/rc
    parsed_version = []
    for part in parts:
        if part.isdigit():
            parsed_version.append(int(part))
        else:
            # Handle alpha, beta, rc as tuples (e.g., ('alpha', 1))
            if 'alpha' in part:
                parsed_version.append(('alpha', int(part.replace('alpha', '')) if part[-1].isdigit() else 0))
            elif 'beta' in part:
                parsed_version.append(('beta', int(part.replace('beta', '')) if part[-1].isdigit() else 0))
            elif 'rc' in part:
                parsed_version.append(('rc', int(part.replace('rc', '')) if part[-1].isdigit() else 0))
            else:
                parsed_version.append(part)  # Fallback for unexpected values

    return tuple(parsed_version)


def export_system_root_certs() -> str:
    """
    Exports macOS system root certificates to a PEM file.
    :return: The path where the PEM file will be.
    """
    cert: Path = Path('/tmp/certs.ca')
    if cert.is_file():
        return cert.as_posix()

    try:
        logger.debug(f'Get system certs from keychain')
        # Define the command to export certificates

        cmd: list = [
            'security',
            'export',
            '-k', '/System/Library/Keychains/SystemRootCertificates.keychain',
            '-t', 'certs',
            '-f', 'pemseq',
            '-o', cert.as_posix()
        ]

        # Execute the command
        logger.debug(' '.join(cmd))
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    except subprocess.CalledProcessError as e:
        logger.critical(f'Error exporting certificates: {e}')

    return cert.as_posix()


def create_logger(name: str = __file__, levels: dict = {}) -> logging.Logger:
    # Create log level
    def make_log_level(level_name: str, level_int: int) -> None:
        logging.addLevelName(level_int, level_name.upper())
        setattr(new_logger, level_name, lambda *args: new_logger.log(level_int, *args))

    new_logger = logging.getLogger(name)

    logging_config: dict = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'stderr': {
                '()': ColourFormat,
                'style': '{', 'format': '{message}',
            },
            'file': {
                'style': '{', 'format': '[{asctime}] [{levelname:8}] {message}'
            }
        },
        'handlers': {
            'stderr': {
                'class': 'logging.StreamHandler',
                'formatter': 'stderr',
                'stream': 'ext://sys.stderr',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'file',
                'filename': options.log_file if options.log_file else '/dev/null',
                'maxBytes': 1024 * 5
                ,
                'backupCount': 0

            }
        },
        'loggers': {
            name: {
                'level': max(((5 - (options.verbosity if options.verbosity >= 0 else options.log_level)) * 10, 0)),
                'handlers': [
                    'stderr'
                ]
            }
        }
    }

    if options.log_file is not None:
        logging_config['loggers'][name]['handlers'].append('file')

    logging.config.dictConfig(logging_config)

    # Create custom levels
    for level in levels.items():
        make_log_level(*level)

    return new_logger


if __name__ == '__main__':
    def valid_path(path):
        parent: Path = Path(path).parent
        if not parent.is_dir():
            print(f'{parent} is not a directory, make it?', end=' ')
            if input('y/n: ').lower()[0] == 'y':
                parent.mkdir(parents=True, exist_ok=True)
                return Path(path)
            raise argparse.ArgumentTypeError(f'{path} is an invalid path')
        return Path(path)


    def parser_formatter(format_class, **kwargs):
        """
        Use a raw parser to use line breaks, etc
        :param format_class: (class) formatting class
        :param kwargs: (dict) kwargs for class
        :return: (class) formatting class
        """
        try:
            return lambda prog: format_class(prog, **kwargs)
        except TypeError:
            return format_class


    # Detect if running as a PyInstaller bundled executable
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundled executable
        executable_directory: Path = Path(sys.executable).parent
        json_files: list = list(executable_directory.glob('*.json'))
        base_path: Path = Path(sys._MEIPASS)
        json_files.extend(list(base_path.glob('*.json')))

    else:
        # Running as a normal Python script
        executable_directory: Path = Path(__file__).parent
        json_files: list = list(executable_directory.glob('*.json'))

    # When in an app, check the resources folder
    if executable_directory.parent.joinpath('Resources').is_dir():
        json_files.extend(list(executable_directory.parent.joinpath('Resources').glob('*.json')))

    # Create argument parser
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=__description__,
        epilog=(
            'Footnotes:\n'
            'If there are .json files in the same directory, each one will be processed and any options provided will the the default settings.\n'
            'Its not highly discouraged not to change the install path of the pkg installers\n'
            'Being vague on blocking apps will result in your install being blocked unnecessarily\n'
            'Error codes:\n'
            '\t1. Unexpected error\n'
            '\t2. Nothing to install\n'
            '\t3. Invalid url\n'
            '\t4. Download error\n'
            '\t7. Could not identify file type\n'
            '\t8. could not unpack archive\n'
            '\t9. errors in one or one runs\n'
        ),
        formatter_class=parser_formatter(argparse.RawTextHelpFormatter,
                                         indent_increment=4, max_help_position=12,
                                         width=160)
    )

    basics_group = parser.add_argument_group('basic options')
    basics_group.add_argument('-u', '--url',
                              action='store', dest='url',
                              required=len(json_files) == 0,
                              help='url to page/download')

    # Use a regex
    url_parser_group = basics_group.add_mutually_exclusive_group()
    url_parser_group.add_argument('-r', '--regex', default=None,
                                  action='store', dest='regex',
                                  help='regex for the the download url from --url (optional)')
    url_parser_group.add_argument('-c', '--code', default=None,
                                  action='store', dest='code',
                                  help='pipe the html from --url into this code (optional)')

    # Specify type to ensure proper run
    types_group = parser.add_argument_group('install type')
    types_parser = types_group.add_mutually_exclusive_group()
    types_parser.add_argument('-t', '--type', default=None,
                              choices=('pkg', 'tar', 'zip', 'dmg'),
                              action='store', dest='file_type',
                              help='specify the download type\ndefault: auto detect')
    types_parser.add_argument('--pkg', default=None, const='pkg',
                              action='store_const', dest='file_type',
                              help='specify that the download type is pkg')
    types_parser.add_argument('--tar', default=None, const='tar',
                              action='store_const', dest='file_type',
                              help='specify that the download type is tar')
    types_parser.add_argument('--zip', default=None, const='zip',
                              action='store_const', dest='file_type',
                              help='specify that the download type is zip')
    types_parser.add_argument('--dmg', default=None, const='dmg',
                              action='store_const', dest='file_type',
                              help='specify that the download type is dmg')

    # Install locations
    dest_group = parser.add_argument_group('install destinations')
    dest_group.add_argument('--pkg-path', type=valid_path, default=Path('/'),
                            action='store', dest='pkg_install_path',
                            help='specify the pkg install location \nNot recommended \ndefault: /')

    dest_group.add_argument('--app-path', type=valid_path, default=Path('/Applications'),
                            action='store', dest='app_install_path',
                            help='specify the app install location \ndefault: /Applications')

    extended_group = parser.add_argument_group('extended options')
    # Allow downgrading
    extended_group.add_argument('--allow-downgrade', default=False,
                                action='store_true', dest='allow_downgrade',
                                help='allow the downgrade of an installation')

    # Repair
    extended_group.add_argument('--reinstall', default=False,
                                action='store_true', dest='reinstall',
                                help='reinstall regardless of versions')

    # Run
    extended_group.add_argument('--run', default=False,
                                action='store_true', dest='run',
                                help='if extracting an app, run it afterwards, use with --reinstall to always open the app')

    advanced_group = parser.add_argument_group('advanced options')
    advanced_group.add_argument('--user-agent',
                                default='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
                                action='store', dest='user_agent',
                                help='custom user agent string')

    # blocking app/file
    extended_group.add_argument('-b', '--blocking-app', default=None,
                                action='store', dest='blocking_app',
                                help='do not install if this app can be found running\n'
                                     'Example: "/Applications/My Easy Finder.app/Contents/MacOS/My Easy Finder" \n'
                                     '         This will be blocked if specifying "app", "Finder" or "MacOS"\n'
                                     '         Use: "My Easy Finder.app"'
                                )

    extended_group.add_argument('-B', '--blocking-file', default=None,
                                action='store', dest='blocking_file',
                                help='do not install if this file/directory exists')

    extended_group.add_argument('-R', '--required-file', default=None,
                                action='store', dest='required_file',
                                help='only install if this file/directory exists')

    extended_group.add_argument('-i', '--blocking-case-insensitive', default=False,
                                action='store_true', dest='blocking_app_insensitive',
                                help='allow the blocking app to match any case')

    # Debug/verbosity option
    logging_group = parser.add_argument_group('logging/output')
    verbosity = logging_group.add_mutually_exclusive_group()
    verbosity.add_argument('--debug', default=3,
                           action='store_const', dest='log_level', const=4,
                           help=argparse.SUPPRESS)
    verbosity.add_argument('-v', default=-1,
                           action='count', dest='verbosity',
                           help='verbosity, 1-5, critical to debug')

    # Output
    logging_group.add_argument('--log', type=valid_path,
                               default=None,
                               action='store', dest='log_file',
                               help='output log')

    # Hidden tests and experiments
    parser.add_argument('--copy-method', default='ditto',
                        choices=('shutil', 'ditto', 'cp', 'rsync'),
                        action='store', dest='copy_method',
                        help=argparse.SUPPRESS)

    options = parser.parse_args()
    base_options: argparse.Namespace = argparse.Namespace(**vars(options))

    logger = create_logger()
    logger.debug('Debug ON')
    logger.debug(pprint.pformat(options))

    # Override settings with json files
    if len(json_files) > 0:
        logger.debug(f'{len(json_files)} file(s) to process')
        json_files.sort()
        exit_code = 0
        # Iterate through each JSON file and load it
        for json_file in json_files:
            logger.info(80 * '-')

            # Load json file
            logger.info(f'Loading file {json_file}')
            try:
                with open(json_file, 'r') as f:
                    json_data = json.load(f)
            except json.decoder.JSONDecodeError as err:
                logger.critical(f'Error reading json file {err}')
                continue
            except PermissionError as err:
                logger.critical(f'{err}')
                continue

            # Validate/parse fields
            if json_data['url'] is None:
                logger.critical(f'url is a required field in {json_file.stem}')
                continue

            # Accept only code or regex, not both fields
            if 'regex' in json_data and 'code' in json_data:
                json['regex'] = None

            json_types = {
                'name': str,
                'url': str,
                'regex': str,
                'file_type': str,
                'pkg_install_path': Path,
                'app_install_path': Path,
                'allow_downgrade': bool,
                'reinstall': bool,
                'run': bool,
                'user_agent': str,
                'blocking_app': str,
                'blocking_file': str,
                'blocking_app_insensitive': str,
                'log_level': int,
                'verbosity': int,
                'log_file': str
            }

            # Correcting types in json_data (type casting)
            for key, value in json_data.items():
                if value is None:
                    continue
                expected_type = json_types.get(key)
                if expected_type:
                    try:
                        # Special case for booleans (since bool("False") is True)
                        if expected_type is bool:
                            if isinstance(value, str):
                                value = value.lower()
                            json_data[key] = value in ('true', '1', 1, 'yes')
                        else:
                            json_data[key] = expected_type(value)
                    except (ValueError, TypeError) as err:
                        print(f'Warning: Unable to cast {key} ({value}) to {expected_type.__name__}. Error: {err}')

            title = str(json_data['name']) if 'name' in json_data else json_file.stem
            logger.info(title.center(80, '='))

            #  Merge into default settings
            logger.debug(pprint.pformat(json_data))
            options: argparse.Namespace = argparse.Namespace(**vars(base_options))
            vars(options).update(json_data)

            # Recreate the logger now that we have all the options parsed
            logger = create_logger()
            logger.debug('Debug ON')
            logger.debug(pprint.pformat(options))

            # Run installer
            return_code = main()
            if return_code > 0:
                exit_code = 9
                logger.warning(f'Install {title} exited with {return_code}')
            else:
                logger.info(f'Install {title} exited with {return_code}')
            atexit._run_exitfuncs()

        logger.info(80 * '-')
        sys.exit(exit_code)
    else:
        sys.exit(main())
