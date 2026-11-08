param([ValidateSet('api','web')][string]$Component = 'api')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
if ($Component -eq 'api') {
    $db = Join-Path $root 'tfm-demo.sqlite3'
    if (-not (Test-Path -LiteralPath $db)) { throw 'Ejecuta primero python scripts/prepare_tfm_demo.py' }
    $env:DATABASE_URL = 'sqlite:///' + $db.Replace('\','/')
    $env:AUTH_COOKIE_SECURE = 'false'
    $env:AUTH_ALLOWED_ORIGINS = 'http://127.0.0.1:5179'
    & "$root\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8002
} else {
    Set-Location -LiteralPath (Join-Path $root 'frontend')
    $env:ORQENTIVA_API_TARGET = 'http://127.0.0.1:8002'
    npm run dev -- --host 127.0.0.1 --port 5179 --strictPort
}
