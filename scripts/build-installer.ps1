# Costruisce l'installer Windows standalone di TicketHub AI.
# 1) impacchetta il backend Python con PyInstaller (onedir)
# 2) builda il frontend Electron (electron-vite)
# 3) genera l'installer NSIS (electron-builder), che include il backend bundlato
#
# Prerequisiti: dipendenze già installate (backend/.venv + npm install).
# Uso:  powershell -ExecutionPolicy Bypass -File scripts\build-installer.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$py = Join-Path $backend ".venv\Scripts\python.exe"

Write-Host "==> [1/3] Bundle backend (PyInstaller)…" -ForegroundColor Cyan
& $py -m PyInstaller --noconfirm --clean --name tickethub-backend --onedir `
  --paths "$backend\src" `
  --collect-submodules uvicorn --collect-submodules app --collect-submodules multipart `
  --hidden-import h11 --hidden-import httptools --hidden-import websockets `
  --hidden-import multipart --hidden-import python_multipart `
  --distpath "$backend\dist\pyinstaller" --workpath "$backend\build\pyinstaller" `
  --specpath "$backend\packaging" "$backend\packaging\server_entry.py"

Write-Host "==> [2/3] Build frontend Electron…" -ForegroundColor Cyan
Push-Location (Join-Path $root "apps\desktop")
npm run build
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "electron-vite build fallito" }

Write-Host "==> [3/3] Installer NSIS (electron-builder)…" -ForegroundColor Cyan
npx electron-builder --win
$code = $LASTEXITCODE
Pop-Location
if ($code -ne 0) { throw "electron-builder fallito" }

Write-Host "==> Fatto. Installer in apps\desktop\release\" -ForegroundColor Green
