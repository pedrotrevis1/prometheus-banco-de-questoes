$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "Prometheus" --icon "icon/Prometheus.ico" --paths . --add-data "prometheus/assets/pix_qr.jpg;prometheus/assets" --add-data "icon/prometheus-icon-apple Exports/prometheus-icon-apple-iOS-Default-1024@1x.png;icon/prometheus-icon-apple Exports" prometheus/__main__.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
