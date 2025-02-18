# macos_app_updater

Script to download an app/pkg/dmg, unpack and determine if it needs to be installed

```install_from_url.bash```

Download from a parma link

Usage:

```bash
install_from_url.bash -h

install_from_url.bash <not used> <not used> <not used> <url to download> <optional: install type dmg,pkg,zip,tar>
Example:
install_from_url.bash _ _ _ https://dl.google.com/chrome/mac/universal/stable/GGRO/googlechrome.dmg
```

```install_from_web.bash```

Download by finding a url on page, not nearly as common anymore

Usage:
```bash
install_from_web.bash _ _ _ https://thonny.org/ 'https:[\/A-z0-9\.]+v(\d+\.)+\d+\/thonny-(\d\.)+pkg' -h
install_from_web.bash <not used> <not used> <not used> <url to download> <regex> <optional: install type dmg,pkg,zip,tar>
Example:
install_from_web.bash _ _ _ https://example.com/downloads https:[\/A-z0-9\.]+v(\d+\.)+\d+\/myapp-(\d\.)+pkg
```

## What?

1. Downloads the file
2. Extract the pkg contents, tar file, zip file, or mount dmg
    1. If pkg, read distribution list or pkginfo and see if its installed
    2. If dmg, mount the dmg, if pkg do i.
    3. If tar extract app and copy to Applications, if pkg do i.
    4. If zip extract app and copy to Application, if pkg do i.

## Why?

It can be difficult maintaining software in macOS MDMs. This script can ensure that you are only patching when there is
a patch to apply and avoid user interruptions.\
Also avoid having to fetch and package software for the user to install.

## Improvements?



## State?

No known bugs. Works.

## New

### 1.2

Packages up zip, tar, dmg, pkgs Validates version in Ditribution pkgs, flat pkgs, tar, zips, and dmg