#!/usr/bin/env bash

################################################################################
# install_from_url.bash
# Author: Shane Young
# Date: 2022-05-17
# Revision:	1.1
# Platform: MacOS
#
# Description
#   Download a package and install
#
# Versions
# 1.	Download and install a file
# 1.1   Check mime type if no extension
#       Reformat file and cleanup
#       Proper pkg version verification
#
################################################################################
# Exit Codes
# 1     Unknown file type for the installer/download
# 2     No application in the installer
#
################################################################################

################################################################################
# Environment setup
################################################################################

# Global Variables
BASEPATH="$(/usr/bin/dirname $0)"
BASENAME="$(/usr/bin/basename $0)"

# Create temporary and working directory
WRKDIR="$TMPDIR"
TMPDIR="/tmp/$BASENAME."$(openssl rand -hex 12)
/bin/mkdir -p -m 777 "$TMPDIR"

# Turn off line wrapping:
#printf '\033[?7l'
# Turn on  line wrapping:
#printf '\033[?7h'

# Set window size ex. 100w x 40h
#printf '\033[8;40;100t'

# Set window Title
printf "\033]0;${BASENAME%%.*}\007"

################################################################################
# Help
################################################################################

for arg in "$@"; do
    if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
        echo "$BASENAME <not used> <not used> <not used> <url to download> <optional: install type dmg,pkg,zip,tar>"
        echo "Example:"
        echo "$BASENAME _ _ _ https://dl.google.com/chrome/mac/universal/stable/GGRO/googlechrome.dmg"
        exit 0
    fi
done

################################################################################
# Traps
################################################################################

function exit_trap() {
    # Remove the downloaded vendor supplied DMG file
    if [ -e $TMPDIR ]; then
        logging.info "Cleaning up temporary files\n"

        # Attempt tp unmount if dmg is mounted
        /usr/bin/hdiutil detach $INSTALL_FILES &>/dev/null
        #[ -e $INSTALL_FILES ] && /bin/rm -rf $INSTALL_FILES
        #[ -e $TMPDIR/pkg_files ] && /bin/rm -rf $TMPDIR/pkg_files
        #/bin/rm -rf $TMPDIR
    fi
}
trap exit_trap TERM INT EXIT

################################################################################
# Functions
################################################################################

# Function to print text in colour
function colour() {
    local DATE=$(/bin/date +"%Y-%m-%dT%H:%M:%S")
    local COLOUR_CODE="$1"
    shift
    local LEVEL="$1"
    shift
    local MESSAGE="$*"
    printf "\033[%sm%s [ %-9s] %s \033[0m\n" "${COLOUR_CODE}" "$DATE" "${LEVEL}" "$MESSAGE"
}

# Function for logging
function logging.debug() {
    colour "90" DEBUG "$(printf "$1" "${@:2}")"
}

function logging.info() {
    colour "92" INFO "$(printf "$1" "${@:2}")"
}

function logging.warning() {
    colour "93" WARNING "$(printf "$1" "${@:2}")"
}

function logging.error() {
    colour "91" ERROR "$(printf "$1" "${@:2}")"
}

function logging.critical() {
    colour "97;41" CRITICAL "$(printf "$1" "${@:2}")"
    exit 10
}

function package_install() {
    PKG_INSTALLER=$1
    PKG_FILES=$TMPDIR/pkg_files

    # Unpack files
    /usr/sbin/pkgutil --expand "$PKG_INSTALLER" $PKG_FILES

    # Using reverse logic to avoid reinstalling packages that have components not installed either by default of choice
    local INSTALL=true

    if [ -e $PKG_FILES/Distribution ]; then
        logging.info "Distribution package"
        # Go through installed packes and see if each version is installed


        while read -r LINE; do
            ID=$(echo "$LINE" | grep -oE 'id="[^"]+"' | sed 's/id="//; s/"//g')
            VERSION=$(echo "$LINE" | grep -oE 'version="[^"]+"' | sed 's/version="//; s/"//g')
            PACKAGE_ID=$(echo "$LINE" | grep -oE 'packageIdentifier="[^"]+"' | sed 's/packageIdentifier="//; s/"//g')

            [ ! -z "$PACKAGE_ID" ] && ID=$PACKAGE_ID
            logging.info "Checking package: $ID (Version: $VERSION)"

            # Get installed version
            INSTALLED_VERSION=$(pkgutil --pkg-info "$ID" 2>/dev/null | awk '/version:/ {print $2}')

            if [[ -z "$INSTALLED_VERSION" ]]; then
                logging.info "Package $ID is not installed."
            elif [[ "$VERSION" == "$INSTALLED_VERSION" ]]; then
                logging.info "Package $ID is already up to date (Version: $VERSION)."
                INSTALL=false
            else
                logging.info "Package $ID has an update available: Installed $INSTALLED_VERSION → Available $VERSION"
            fi
        done < <(/usr/bin/xmllint --xpath '//pkg-ref[@version]' "$PKG_FILES/Distribution" | /usr/bin/egrep "^<pkg-ref.*")
    elif [ -e $PKG_FILES/PackageInfo ]; then
        logging.info "Single package"
        ID=$(xmllint --xpath 'string(/pkg-info/@identifier)' $PKG_FILES/PackageInfo)
        VERSION=$(xmllint --xpath 'string(/pkg-info/@version)' $PKG_FILES/PackageInfo)

        logging.info "Checking package: $ID (Version: $VERSION)"

        if [[ -z "$INSTALLED_VERSION" ]]; then
            logging.info "Package $ID is not installed."
        elif [[ "$VERSION" == "$INSTALLED_VERSION" ]]; then
            logging.info "Package $ID is already up to date (Version: $VERSION)."
            INSTALL=false
        else
            logging.info "Package $ID has an update available: Installed $INSTALLED_VERSION → Available $VERSION"
        fi
    fi

    if $INSTALL; then
        logging.info "Installing"
        installer -pkg $PKG_INSTALLER -target /
        exit $?
    else
        logging.info "No install required"
    fi
}

################################################################################
# Main
################################################################################

NOW=$(/bin/date +"%Y-%m-%dT%H-%M-%S")
INSTALLER=$TMPDIR/install-$NOW

# Url to pull the dmg from
URL=${4}
[ "$URL" == "" ] && logging.critical "No url"

# Download vendor supplied DMG file into /tmp/
logging.info "Downloading %s ...\n" $URL
/usr/bin/curl -L ${URL} -o $INSTALLER

if [ $? -gt 0 ]; then
    logging.critical "Error downloading file"
fi

FILE_TYPE=""

# Check if the filetype is explicitly specified
if [ "$FILE_TYPE" == "" ]; then
    FILE_TYPE=${5}
    logging.debug "File type explict mention: %s\n" $FILE_TYPE
fi

# Check files extension
if [ "$FILE_TYPE" == "" ]; then
    FILE_NAME="${URL##*/}"
    FILE_TYPE="${FILE_NAME##*.}"

    # Check for no extension
    [[ "$FILE_NAME" == "$FILE_TYPE" ]] && FILE_TYPE=""
    logging.debug "File type from extension: %s\n" $FILE_TYPE
fi

# Check files mimetype in last ditch attempt
if [ "$FILE_TYPE" == "" ]; then
    MIME_TYPE=$(/usr/bin/file --mime -z $INSTALLER)
    if [[ "${MIME_TYPE}" == *x-apple-diskimage* ]]; then
        FILE_TYPE=dmg
    elif [[ "${MIME_TYPE}" == *x-tar* ]]; then
        FILE_TYPE=tar.gz
    elif [[ "${MIME_TYPE}" == *x-xar* ]]; then
        FILE_TYPE=pkg
    elif [[ "${MIME_TYPE}" == *zip* ]]; then
        FILE_TYPE=zip
    else
        logging.error "Unknown file type: ${MIME_TYPE}"
        exit 1
    fi
fi

# Rename the file with extension
/bin/mv "${INSTALLER}" "${INSTALLER}.${FILE_TYPE}"
INSTALLER="${INSTALLER}.${FILE_TYPE}"

logging.info "Downloaded %s\n" $INSTALLER

# Handle package
if [ "$FILE_TYPE" == pkg ]; then
    # Install the pkg
    logging.info "Installing PKG %s ...\n" $INSTALLER
    package_install $INSTALLER
    exit 0
fi

# Directory to unpack or mount files into
INSTALL_FILES=$TMPDIR/install_files
/bin/mkdir $INSTALL_FILES

# Unpack dmg
if [ "$FILE_TYPE" == dmg ]; then
    # Install the pkg
    logging.info "Opening DMG %s ...\n" $INSTALLER
    /usr/bin/hdiutil attach -nobrowse -mountpoint $INSTALL_FILES $INSTALLER
fi

# unpack tar
if [[ "$FILE_TYPE" == tar* ]]; then
    # Install the pkg
    logging.info "Unpacking TAR %s ...\n" $INSTALLER
    tar -xf $INSTALLER -C $INSTALL_FILES
fi

# unpack tar
if [ "$FILE_TYPE" == zip ]; then
    # Install the pkg
    logging.info "Unpacking ZIP %s ...\n" $INSTALLER
    unzip $INSTALLER -d $INSTALL_FILES &>/dev/null
fi

# Do we install
INSTALL=false

# Handle install files
# Find the first .app bundle inside $INSTALL_FILES
APP_PATH=$(find "$INSTALL_FILES" -maxdepth 2 -type d -name "*.app" | head -n 1)
if [[ -z "$APP_PATH" ]]; then
    logging.warning "No .app bundle found in $INSTALL_FILES"

    # If no app try to find an installer
    PKG_PATH=$(find "$INSTALL_FILES" -maxdepth 2 -size +500c -type f -name "*.pkg" ! -name ".*" | head -n 1)
    if [[ -z "$PKG_PATH" ]]; then
        logging.critical "No .pkg bundle found in $INSTALL_FILES"
        exit 2
    else
        # Handle install
        logging.info "Installing PKG %s ...\n" $PKG_PATH
        package_install $PKG_PATH
        exit $?
    fi
fi

# Ge the app install and destination
APP_NAME=$(basename "$APP_PATH")
DEST_APP="/Applications/$APP_NAME"

logging.debug "New app \"%s\"\n" "$APP_NAME"
logging.debug "Install location \"%s\"\n" "$DEST_APP"

# Get the version of the app from $INSTALL_FILES
NEW_VERSION=$(defaults read "$APP_PATH/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null)
[ -z "$NEW_VERSION" ] && NEW_VERSION="unknown"

logging.debug "Install version %s\n" "$NEW_VERSION"

# Check if the app already exists in /Applications
if [[ -d "$DEST_APP" ]]; then
    CURRENT_VERSION=$(defaults read "$DEST_APP/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null)
    [[ -z "$CURRENT_VERSION" ]] && CURRENT_VERSION="unknown"

    logging.debug "Current version %s\n" "$CURRENT_VERSION"

    # Compare versions
    if [[ "$CURRENT_VERSION" == "$NEW_VERSION" ]]; then
        logging.info "Same version already installed. Skipping copy."
        exit 0
    else
        INSTALL=true
    fi
else
    INSTALL=true
fi

if $INSTALL; then
    logging.info "Installing application, upgrading from %s to %s\n" "$CURRENT_VERSION" "$NEW_VERSION"
    cp -Rp "$APP_PATH" /Applications/
fi

exit 0
