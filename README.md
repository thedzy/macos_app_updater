# macos_app_updater


## Overview

`install_from_web.py` is a versatile, feature-rich script designed to simplify the process of downloading, installing, updating, and managing macOS applications directly from the web. It was created to provide a flexible solution that allows anyone to create configuration files or specify options for automating application updates—whether for personal use, sharing, or enterprise environments. This tool is ideal for system administrators, MDM environments, or any user who wants to keep their macOS software up to date with minimal effort. It supports a wide range of package types, robust version detection, and automated actions based on specified conditions.

### Supported Package Types
- **PKG (Package Files):** Standard macOS installation packages, including flat PKGs and distribution PKGs.
- **DMG (Disk Images):** Mounted automatically, with applications extracted and installed.
- **ZIP Archives:** Extracted automatically, with applications or installation packages processed.
- **TAR Archives:** Automatically extracted, including tar.gz and tar.bz2 formats.

### Intelligent Version Detection
- The script can detect and compare versions of existing applications against the newly downloaded version:
  - **DMG Applications:** Reads `Info.plist` for `CFBundleShortVersionString`.
  - **PKG Packages:** Reads the version directly from the `Distribution` or `PackageInfo` file.
  - **ZIP and TAR Archives:** Extracts and inspects version information based on the contents.
- Automatically detects if the installed version is newer, older, or identical, and takes action based on user settings.

### Automatic Package Type Detection
- If the user does not specify the package type, the script intelligently determines the type using:
  - User-provided type (if specified).
  - File extension (e.g., `.dmg`, `.pkg`, `.zip`, `.tar`).
  - MIME type detection (using file headers).
  - Magic number (file signature) detection for robust identification.

### Automated Installation and Updating
- Downloads the application or package from the specified URL.
- Automatically determines the most suitable installation method based on the package type:
- Verifies the version of the existing installation and only updates if:
  - The new version is newer.
  - The new version is different and `--reinstall` is specified.
  - The new version is older, but `--allow-downgrade` is specified.

### Flexible Customization and Control
- Supports specifying installation paths for both applications and packages.
- Allows blocking installations if specified applications are running (`--blocking-app`) or files/directories exist (`--blocking-file`).
- Can be configured to only install if specific files exist (`--required-file`).
- Offers advanced options for custom user agents (`--user-agent`) and custom download parsing:
  - Regular expression-based extraction (`--regex`).
  - Custom shell code for complex parsing (`--code`).

### Logging and Debugging
- Verbose logging with customizable verbosity levels.
- Supports saving logs to a file (`--log LOG_FILE`).

### Bulk Configuration with JSON Files
- Multiple configurations can be processed using JSON files placed in the same directory as the script.
- Each JSON file can define an installation, including all available options:
  - URL, regex, code, file type, installation paths, blocking conditions, etc.
- This allows for bulk management and deployment of multiple applications in one run.

### Designed for Automation and Integration
- Can be run as a standalone script
- Cnn be compiled into a standalone binary for easy distribution.
- Cnn be compiled into a standalone application.
- Cnn be compiled into a standalone pkg.
- Ideal for use in MDM environments, allowing automated, policy-based installation and updating.
- Can be easily integrated into scripts or automated workflows.

### Why Use This Script?
- Simplifies software management for macOS systems.
- Avoids unnecessary user interruptions by only installing or updating when needed.
- Ensures that applications are always up to date, without manual intervention.
- Supports advanced use cases like custom download extraction methods and bulk installations.
- Fully compatible with MDM environments, making it ideal for enterprise deployments.

### Who is it For?
- System administrators managing multiple macOS systems.
- Advanced users who prefer automation over manual installation.
- MDM administrators who need a flexible, scriptable way to manage application installations.
- Anyone who wants to keep their macOS software up to date effortlessly.
---

## Usage

```console
% python3 install_from_web.py -h
usage: install_from_web.py [-h] -u URL [-r REGEX | -c CODE] [-t {pkg,tar,zip,dmg} | --pkg | --tar | --zip | --dmg] [--pkg-path PKG_INSTALL_PATH]
                           [--app-path APP_INSTALL_PATH] [--allow-downgrade] [--reinstall] [--run] [--user-agent USER_AGENT] [-b BLOCKING_APP]
                           [-B BLOCKING_FILE] [-R REQUIRED_FILE] [-i] [-v] [--log LOG_FILE]

    install_from_web.py: 
    Install applications directly from the web
    

options:
    -h, --help
            show this help message and exit

basic options:
    -u, --url URL
            url to page/download
    -r, --regex REGEX
            regex for the the download url from --url (optional)
    -c, --code CODE
            pipe the html from --url into this code (optional)

install type:
    -t, --type {pkg,tar,zip,dmg}
            specify the download type
            default: auto detect
    --pkg   specify that the download type is pkg
    --tar   specify that the download type is tar
    --zip   specify that the download type is zip
    --dmg   specify that the download type is dmg

install destinations:
    --pkg-path PKG_INSTALL_PATH
            specify the pkg install location 
            Not recommended 
            default: /
    --app-path APP_INSTALL_PATH
            specify the app install location 
            default: /Applications

extended options:
    --allow-downgrade
            allow the downgrade of an installation
    --reinstall
            reinstall regardless of versions
    --run   if extracting an app, run it afterwards, use with --reinstall to always open the app
    -b, --blocking-app BLOCKING_APP
            do not install if this app can be found running
            Example: "/Applications/My Easy Finder.app/Contents/MacOS/My Easy Finder" 
                     This will be blocked if specifying "app", "Finder" or "MacOS"
                     Use: "My Easy Finder.app"
    -B, --blocking-file BLOCKING_FILE
            do not install if this file/directory exists
    -R, --required-file REQUIRED_FILE
            only install if this file/directory exists
    -i, --blocking-case-insensitive
            allow the blocking app to match any case

advanced options:
    --user-agent USER_AGENT
            custom user agent string

logging/output:
    -v      verbosity, 1-5, critical to debug
    --log LOG_FILE
            output log

Footnotes:
If there are .json files in the same directory, each one will be processed and any options provided will the the default settings.
Its not highly discouraged not to change the install path of the pkg installers
Being vague on blocking apps will result in your install being blocked unnecessarily
Error codes:
	1. Unexpected error
	2. Nothing to install
	3. Invalid url
	4. Download error
	7. Could not identify file type
	8. could not unpack archive
	9. errors in one or one runs

```

Examples:
```
# 1Password pkg and app
install_from_web.py --url 'https://downloads.1password.com/mac/1Password.pkg'
install_from_web.py --url 'https://downloads.1password.com/mac/1Password.zip' --reinstall --app-location /tmp --run

# Alfred
install_from_web.py --url "https://www.alfredapp.com/" --regex "https://cachefly.alfredapp.com/Alfred_5.([0-9_]+\.)+dmg"

# Audacity
install_from_web.py --url "https://www.audacityteam.org/download/mac/" --regex "https://github.com/audacity/audacity/releases/download/Audacity-[0-9\.]+/audacity-macOS-[0-9\.]+-universal.pkg"

# BBedit
install_from_web.py --url 'https://www.barebones.com/products/bbedit/download.html'  --regex '[^"]+BBEdit_(\d+\.)+dmg'

# Blender
install_from_web.py --url 'https://www.blender.org/download/' --code 'egrep -o "https://www.blender.org/download/release/Blender4.4/blender-(\d+\.)+\d+-macos-arm64.dmg" | tail -n 1 | sed "s:www.blender.org/download:mirrors.iu13.net/blender:g"'

# Brave
install_from_web.py --url 'https://referrals.brave.com/latest/BRV010/Brave-Browser.dmg'

# Cakebrew
install_from_web.py --url 'https://www.cakebrew.com/' --regex 'https://cakebrew-377a.kxcdn.com/cakebrew-(\d+\.)+zip'

# Cyberduck
install_from_web.py --url 'https://cyberduck.io/download/' --regex 'https://update.cyberduck.io/Cyberduck-[0-9\.]+.zip' -b Cyberduck.app

# Discord
install_from_web.py --url 'https://discord.com/api/download?platform=osx'

# Dropbox
install_from_web.py --url 'https://www.dropbox.com/download?os=mac&plat=mac'

# Firefox
install_from_web.py --url 'https://download.mozilla.org/?product=firefox-latest-ssl&os=osx&lang=en-US'

# Go lang
install_from_web.py --url 'https://go.dev/dl/' --regex '[^"]+go\d+\.\d+\.\d+\.darwin-arm64.pkg'

# Google Chrome
install_from_web.py --url 'https://dl.google.com/chrome/mac/universal/stable/GGRO/googlechrome.dmg'

# Google Drive
install_from_web.py --url 'https://dl.google.com/drive-file-stream/GoogleDrive.dmg'

# Hexfiend 
install_from_web.py --url 'https://hexfiend.com/' --regex '[^"]+Hex_Fiend_(\d++\.)+dmg'

# Nodejs
install_from_web.py --url 'https://nodejs.org/dist/latest/' --regex '/dist/latest/node-v(\d+\.)+pkg'
# Nodejs (Exactly the same as above)
install_from_web.py --url 'https://nodejs.org/dist/latest/' --code 'egrep -o "/dist/latest/node-v(\d+\.)+pkg"'

# Spotify
install_from_web.py --url 'https://download.scdn.co/SpotifyInstaller.zip'

# Steam
install_from_web.py --url 'https://cdn.fastly.steamstatic.com/client/installer/steam.dmg' --run

# Suspicious Package
install_from_web.py --url 'https://mothersruin.com/software/downloads/SuspiciousPackage.dmg'

# Thonny
install_from_web.py --url 'https://thonny.org/' --regex 'https:[\/A-z0-9\.]+v(\d+\.)+\d+\/thonny-(\d\.)+pkg'

# Visual studio code
install_from_web.py --url 'https://code.visualstudio.com/sha/download?build=stable&os=darwin-universal'

# VLC
install_from_web.py --url 'https://mirror.xenyth.net/videolan/vlc/last/macosx/' --regex '[^"]+arm64.dmg'

# Wireshark
install_from_web.py --url 'https://www.wireshark.org/download.html' --regex '[^"]+Arm%2064.dmg'

# Zoom
install_from_web.py --url 'https://zoom.us/client/6.4.6.53970/zoomusInstallerFull.pkg?archType=arm64'

```
## Build python independent executable the can include multiple config for updating and installing
```
pyinstaller -y /Users/syoung/git/macos_app_updater/installer_bin.spec
```

## Build python independent app that can include multiple config for updating and installing
```
pyinstaller -y /Users/syoung/git/macos_app_updater/installer_app.spec
```

## Build python independent pkg that can include multiple config for updating and installing
```
pyinstaller -y /Users/syoung/git/macos_app_updater/installer_app.spec
```



## TL;DR?

1. Downloads the file or page.
2. Finds the download link (using regex or custom code if needed).
3. Detects file type automatically.
4. Checks the version.
5. Installs or updates only if necessary.


## Why?

Maintaining software in macOS MDMs can be challenging. This script ensures that software is only patched when an update is available, minimizing user interruptions. It also eliminates the need to manually fetch and package software for users. 

Most importantly, it is fully user-configurable—no dependency on anyone else to update configurations or set options tailored to your needs.

## Improvements?

github url specific downloading


## State?

No known bugs. Works.

## New

### 1.0

- Supports installation of multiple package types:
  - **ZIP**, **TAR**, **DMG**, and **PKG**.
- Automatic file type detection:
  - MIME type analysis.
  - File signature detection (first 16 bytes).
  - User-specified file type as an override.
- Comprehensive version validation:
  - Reads version from `Distribution` and `PackageInfo` in PKG files.
  - Reads version from `Info.plist` for macOS apps.
  - Custom version parsing for complex version formats.
- Configurable installation paths:
  - Separate paths for PKG and APP installations.
- Automated installation logic:
  - Installs only if newer version is detected.
  - Optional forced reinstallation.
  - Supports downgrades if explicitly allowed.
- Advanced blocking conditions:
  - Can block installation if a specified app is running.
  - Can block if a specified file exists.
  - Can require a specified file to exist.
- Enhanced logging:
  - Configurable log file and verbosity levels.
  - Colour-coded console logging.
- JSON configuration support:
  - Load multiple JSON configurations for batch installations.
- Secure HTTPS downloading:
  - Custom SSL context with system root certificates.
- Regex and shell command support for dynamic download link detection.