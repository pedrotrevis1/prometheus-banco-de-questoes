$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "Prometheus" --paths . --add-data "prometheus/assets/pix_qr.jpg;prometheus/assets" prometheus/__main__.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
