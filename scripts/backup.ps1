param([string]$Name = ('demo-' + (Get-Date -Format 'yyyyMMdd-HHmmss')))
$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($Name -notmatch '^[a-zA-Z0-9_-]+$') { throw 'Use only letters, digits, underscores and hyphens for backup names.' }
New-Item -ItemType Directory -Force backups | Out-Null
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/coordination.dump'
if ($LASTEXITCODE) { throw 'Database backup failed.' }
docker compose cp db:/tmp/coordination.dump "backups/$Name.dump"
if ($LASTEXITCODE) { throw 'Backup copy failed.' }
if (Test-Path backend/private) { Compress-Archive -Path backend/private -DestinationPath "backups/$Name-files.zip" }
Write-Host "Backup saved: backups/$Name.dump (keep any matching files archive with it)"
