#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ARCHIVE="$PACKAGE_DIR/linux-runtime.tar.gz"
INSTALL_PARENT="${PATHPOCKET_INSTALL_PARENT:-$HOME/Applications/PathPocket-v1.0.6}"
INSTALL_PARENT="${INSTALL_PARENT/#\$HOME/$HOME}"
INSTALL_ROOT="$INSTALL_PARENT/PathPocket_v1.0.6_Linux"
PROJECT_ROOT="${PATHPOCKET_PROJECT_ROOT:-$HOME/PathPocket Projects}"
PROJECT_ROOT="${PROJECT_ROOT/#\$HOME/$HOME}"

test -f "$ARCHIVE" || { echo "Missing Linux runtime archive: $ARCHIVE" >&2; exit 2; }
mkdir -p "$INSTALL_PARENT"

if test -e "$INSTALL_ROOT"; then
  echo "Existing PathPocket v1.0.6 installation found at $INSTALL_ROOT"
  echo "Reapplying the same package files; existing runtime/downloads are preserved for resume."
fi
tar -xzf "$ARCHIVE" -C "$INSTALL_PARENT"

cd "$INSTALL_ROOT"
bash Verify_Package.sh
bash Setup_First_Run.sh
bash Verify_Installation.sh --quick

mkdir -p "$PROJECT_ROOT"
printf '%s\n' "$INSTALL_ROOT" > "$HOME/.pathpocket_hf5_install_root"
echo "PathPocket WSL2 installation: PASS"
echo "Installation root: $INSTALL_ROOT"
echo "Suggested project root: $PROJECT_ROOT"
