param([switch]$Prepare)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
docker compose up -d db
if ($LASTEXITCODE) { throw 'Start Docker Desktop and retry.' }
if ($Prepare) {
    docker compose build
    if ($LASTEXITCODE) { throw 'Container build failed.' }
}
docker compose run --rm api python manage.py migrate
if ($LASTEXITCODE) { throw 'Migration failed.' }
if ($Prepare) {
    docker compose run --rm -e HF_HUB_OFFLINE=0 api python manage.py download_model
    if ($LASTEXITCODE) { throw 'Model download failed.' }
    docker compose run --rm api python manage.py seed_demo
    docker compose run --rm api python manage.py evaluate_matching --data /data/evaluation.json --output /reports/matching.json
    docker compose run --rm api python manage.py match_pending
    Push-Location frontend
    npm.cmd ci
    Pop-Location
}
docker compose up -d api worker
if ($LASTEXITCODE) { throw 'Application startup failed.' }
Write-Host 'API is ready. Starting the interface at http://127.0.0.1:5173'
Set-Location frontend
npm.cmd run dev
