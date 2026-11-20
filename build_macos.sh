#!/bin/sh
set -eu
cd "$(dirname "$0")"

if [ "$(uname -s)" != "Darwin" ]; then
  printf '%s\n' "O build para macOS deve ser executado em um Mac." >&2
  exit 1
fi

python -m PyInstaller --noconfirm --clean packaging/macos/Prometheus.spec
