#!/bin/sh
set -eu
cd "$(dirname "$0")"

python -m PyInstaller --noconfirm --clean --onefile --windowed \
  --name "Prometheus" \
  --icon "icon/prometheus-icon-apple Exports/prometheus-icon-apple-iOS-Default-1024@1x.png" \
  --osx-bundle-identifier "com.pedrotrevisan.prometheus" \
  --paths . \
  --add-data "prometheus/assets/pix_qr.jpg:prometheus/assets" \
  --add-data "icon/prometheus-icon-apple Exports/prometheus-icon-apple-iOS-Default-1024@1x.png:icon/prometheus-icon-apple Exports" \
  prometheus/__main__.py
