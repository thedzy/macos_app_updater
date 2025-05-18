# macos_app_updater

Script to download an app/pkg/dmg/tar/zip, unpack and determine if it needs to be installed

```install_from_web```

Download from a parma link or lind the link on a page.  Install ONLY if it is missing or requires an update.

Usage:

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
    -u URL, --url URL
            url to page/download
    -r REGEX, --regex REGEX
            regex for the the download url from --url (optional)
    -c CODE, --code CODE
            pipe the html from --url into this code (optional)

install type:
    -t {pkg,tar,zip,dmg}, --type {pkg,tar,zip,dmg}
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
    -b BLOCKING_APP, --blocking-app BLOCKING_APP
            do not install if this app can be found running
            Example: "/Applications/My Easy Finder.app/Contents/MacOS/My Easy Finder" 
                     This will be blocked if specifying "app", "Finder" or "MacOS"
                     Use: "My Easy Finder.app"
    -B BLOCKING_FILE, --blocking-file BLOCKING_FILE
            do not install if this file/directory exists
    -R REQUIRED_FILE, --required-file REQUIRED_FILE
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
## Build python independent executable, can include multiple config for updating and installing
```
pyinstaller -y /Users/syoung/git/macos_app_updater/installer_bin.spec
```

## Build python independent app that includes, can include multiple config for updating and installing
```
pyinstaller -y /Users/syoung/git/macos_app_updater/installer_app.spec
```


## What?

1. Downloads the file/page
   - Optionally regex the page for teh download link
2. Check the mime type by
   1. Accepting teh user selected type
   2. Reading the extension
   3. Reading the first 16 characters of the file
3. If dmg, zip or tar, mount/extract the contents and check for .app or pkg 
   1. If pkg dead the distribution file and pkginfo to check the version and verify it's an update
   2. If app, read the app contents and check the version and verify it's an update


## Why?

It can be difficult maintaining software in macOS MDMs. This script can ensure that you are only patching when there is
a patch to apply and avoid user interruptions.\
Also avoid having to fetch and package software for the user to install.

## Improvements?



## State?

No known bugs. Works.

## New

### 1.0

Packages up zip, tar, dmg, pkgs Validates version in Ditribution pkgs, flat pkgs, tar, zips, and dmg