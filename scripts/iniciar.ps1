# Arranca todo lo necesario para desarrollar con un solo comando:
#
#   .\scripts\iniciar.ps1
#
# 1. PostgreSQL en Docker (compose.yaml, usa POSTGRES_PASSWORD del archivo .env).
# 2. Migraciones pendientes de la base de datos.
# 3. La API (puerto 8001) y la web (puerto 5178), cada una en su propia ventana.
# Para detenerlo: cierra las dos ventanas; PostgreSQL sigue en marcha hasta "docker compose stop".
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

Write-Host "1/3 Iniciando PostgreSQL en Docker..."
docker compose up -d --wait postgres
if ($LASTEXITCODE -ne 0) { throw "No se pudo iniciar PostgreSQL. Comprueba que Docker Desktop este abierto y que .env tenga POSTGRES_PASSWORD." }

Write-Host "2/3 Aplicando migraciones..."
& "$projectRoot\.venv\Scripts\python.exe" -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw "Fallaron las migraciones. Revisa el mensaje anterior." }

Write-Host "3/3 Abriendo la API y la web en ventanas nuevas..."
# Las ventanas son de cmd para no depender de la politica de ejecucion de scripts de PowerShell
# (npm falla en PowerShell cuando los scripts estan deshabilitados). Heredan estas variables.
$env:AUTH_COOKIE_SECURE = "false"
$env:AUTH_ALLOWED_ORIGINS = "http://127.0.0.1:5178,http://localhost:5178"
Start-Process -FilePath "cmd.exe" -WorkingDirectory $projectRoot -ArgumentList "/k", "title ORQENTIVA API && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001"
Start-Process -FilePath "cmd.exe" -WorkingDirectory (Join-Path $projectRoot "frontend") -ArgumentList "/k", "title ORQENTIVA WEB && npm run dev -- --host 127.0.0.1 --port 5178 --strictPort"

Write-Host ""
Write-Host "Listo. Cuando la ventana WEB muestre 'ready', abre http://127.0.0.1:5178/ (panel: http://127.0.0.1:5178/#access)"
