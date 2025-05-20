#!/usr/bin/env bash

set -e

################################################################################
# make_pkg_installer.sh
# Author: Shane Young
# Date: 2025-05-19
# Revision:	1.0
# Platform: MacOS
#
# Description
# Make a pkg installer using the install_from_web
# Bundle json configs to install one or many applications
# Create a package to run the install_from_web
# --pyinstaller <path>: Path to pyinstaller, needed if using a venv.
# --debug: Enable debugging messages.
# -h/--help print this
#
# Versions
# 1.	Create pkg
#
################################################################################
# Exit Codes
#
################################################################################

################################################################################
# Environment setup
################################################################################

# Global Variables
BASEPATH="$(dirname $0)"
BASENAME="$(basename $0)"

# Create temporary and working directory
WRKDIR="$TMPDIR"
TMPDIR="/tmp/$BASENAME."$(openssl rand -hex 12)
/bin/mkdir -p -m 777 "$TMPDIR"

# Set window Title
printf "\033]0;${BASENAME%%.*}\007"

################################################################################
# Traps
################################################################################

function exit_trap() {
    # Restore the cursor
   rm -rf $PKG_DIR
}
trap exit_trap TERM INT EXIT


################################################################################
# Functions
################################################################################

LOG_LEVEL=1

# Function to print text in colour
function colour() {
    local DATE=$(date +"%Y-%m-%dT%H:%M:%S")
    local COLOUR_CODE="$1"
    shift
    local LEVEL="$1"
    shift
    local MESSAGE="$*"
    printf "\033[%sm%s [ %-9s] %s \033[0m\n" "${COLOUR_CODE}" "$DATE" "${LEVEL}" "$MESSAGE"
}

# Function for logging
function logging.debug() {
    [ $LOG_LEVEL -gt 0 ] && return
    colour "90" DEBUG "$(printf -- "${@}")"
}

function logging.info() {
    [ $LOG_LEVEL -gt 1 ] && return
    colour "92" INFO "$(printf -- "${@}")"
}

function logging.warning() {
  [ $LOG_LEVEL -gt 2 ] && return
    colour "93" WARNING "$(printf -- "${@}")"
}

function logging.error() {
  [ $LOG_LEVEL -gt 3 ] && return
    colour "91" ERROR "$(printf -- "${@}")"
}

function logging.critical() {
    colour "97;41" CRITICAL "$(printf -- "${@}")"
    exit 1
}




################################################################################
# Arguments
################################################################################


# Collect all parameters without definitions
POSITIONAL=()

while [[ $# -gt 0 ]]; do
    case "$1" in
    --*)
        VAR="${1#*--}"
        shift
        if [[ "$1" == -* ]] || [[ -z "$1" ]]; then
            declare "$VAR"=true
        else
            declare "$VAR"="$1"
            shift
        fi
        ;;
    -*)
        VAR="${1#*-}"
        shift
        if [[ "$1" == -* ]] || [[ -z "$1" ]]; then
            declare "$VAR"=true
        else
            declare "$VAR"="$1"
            shift
        fi
        ;;
    *)
        POSITIONAL+=("$1")
        shift
        ;;
    esac
done



################################################################################
# Main
################################################################################


if [ "$help" ]; then
  logging.info "$BASENAME"
  logging.info "Create a package to run the install_from_web"
  logging.info "--pyinstaller <path>: Path to pyinstaller, needed if using a venv."
  logging.info "--debug: Enable debugging messages."
  logging.info "-h/--help print this"
  exit 0
fi

[ "$debug" ] && LOG_LEVEL=0 || LOG_LEVEL=1

# Directory structure
PKG_DIR="/tmp/macos_app_updater_pkg"
RESOURCES_DIR="$PKG_DIR/Resources"
PAYLOAD_DIR="$PKG_DIR/Payload"
SPEC_PATH="$BASEPATH/installer_bin.spec"

# Create directory structure
logging.debug "Create folders"
mkdir -p "$RESOURCES_DIR"
mkdir -p "$PAYLOAD_DIR"

# Copy the binary to the payload
logging.debug "Using ${pyinstaller} to process $SPEC_PATH "
logging.info "Processing $SPEC_PATH, question to follow, use default name"
${pyinstaller:-pyinstaller} -y "$SPEC_PATH"

logging.debug "Copy binary to package directory"
cp -p "$(pwd)/dist/install_from_web" "$PAYLOAD_DIR"


# Create the preinstall script (Empty since we don't need pre-setup)
logging.debug "Creating preinstall script"
cat << 'EOF' > "$RESOURCES_DIR/preinstall"
#!/bin/bash
echo "Running preinstall script..."
# Add custom code here, although you should not need anything
exit 0
EOF
chmod +x "$RESOURCES_DIR/preinstall"

# Create the postinstall script (Runs the binary)
logging.debug "Creating postinstall script"
cat << 'EOF' > "$RESOURCES_DIR/postinstall"
#!/bin/bash
echo "Running install_from_web ..."

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
cp /tmp/install_from_web "$TEMP_DIR/install_from_web"
chmod +x "\$TEMP_DIR/install_from_web"

# Run the binary
"$TEMP_DIR/install_from_web" --debug

# Clean up
rm -rf "$TEMP_DIR"
echo "Installation complete."
exit 0
EOF
chmod +x "$RESOURCES_DIR/postinstall"


# Build the .pkg using pkgbuild
logging.info "Building package"
pkgbuild --root "$PAYLOAD_DIR" \
         --scripts "$RESOURCES_DIR" \
         --identifier ${indentifier:-com.thedzy.install_from_web} \
         --version "1.0" \
         --install-location "/tmp" \
         "$PKG_DIR/install_from_web.pkg"


mv "$PKG_DIR/install_from_web.pkg" "$(pwd)/install_from_web.pkg"

echo "$(pwd)/install_from_web.pkg"

exit 0
