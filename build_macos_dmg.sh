#!/bin/sh
set -eu
cd "$(dirname "$0")"

# Package an existing app only. This command never invokes PyInstaller.
python packaging/macos/dmg.py "$@"
