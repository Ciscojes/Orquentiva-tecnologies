param([ValidateSet("api", "web")][string]$Component = "api")
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if ($Component -eq "api") {
    $env:AUTH_COOKIE_SECURE = "false"
    $env:AUTH_ALLOWED_ORIGINS = "http://127.0.0.1:5178,http://localhost:5178"
    & "$projectRoot\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001
} else {
    Set-Location -LiteralPath (Join-Path $projectRoot "frontend")
    npm run dev -- --host 127.0.0.1 --port 5178 --strictPort
}
