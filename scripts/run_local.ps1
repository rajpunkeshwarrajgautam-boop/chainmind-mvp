# Run the API locally without Docker (SQLite + in-process Celery).
# Usage: .\scripts\run_local.ps1
# Then: http://127.0.0.1:8000/docs

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$env:ENVIRONMENT = "development"
$env:DATABASE_URL = if ($env:DATABASE_URL) { $env:DATABASE_URL } else { "sqlite:///./chainmind-local.db" }
$env:JWT_SECRET = if ($env:JWT_SECRET) { $env:JWT_SECRET } else { "local-dev-jwt-secret-minimum-32-characters" }
$env:CELERY_TASK_ALWAYS_EAGER = "true"
# Optional: install Redis and set REDIS_URL so /ready returns 200; otherwise /ready may show redis:false.
if (-not $env:REDIS_URL) { $env:REDIS_URL = "redis://127.0.0.1:6379/0" }

Write-Host "Starting ChainMind at http://127.0.0.1:8000/docs (Ctrl+C to stop)"
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
