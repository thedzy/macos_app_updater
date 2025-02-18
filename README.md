# macos_app_updater

Script to download an app/pkg/dmg, unpack and determine if it needs to be installed

```install_from_url.bash```

Usage:

```bash
install_from_url.bash -h

install_from_url.bash <not used> <not used> <not used> <url to download> <optional: install type dmg,pkg,zip,tar>
Example:
install_from_url.bash _ _ _ https://dl.google.com/chrome/mac/universal/stable/GGRO/googlechrome.dmg
```

## What?

1. Downloads the file
2. Extract the pkg contents, tar file, zip file, or mount dmg
    1. If pkg, read distribution list or pkginfo and see if its installed
    2. If dmg, mount the dmg, if pkg do i.
    3. If tar extract app and copy to Applications, if pkg do i.
    4. If zip extract app and copy to Application, if pkg do i.

## Why?

It can be difficult maintaining software in macOS MDMs.  This script can ensure that you are only patching when there is a patch to apply and avoid user interruptions.\
Also avoid having to fetch and package software for the user to install.

## Improvements?
There is a 2ns part to thsi where it gets the file from a regex, but that needs cleaning up before posting

## State?

No known bugs. Works.

## New

### 1.2

Packages up zip, tar, dmg, pkgs
Validates version in Ditribution pkgs, flat pkgs, tar, zips, and dmg