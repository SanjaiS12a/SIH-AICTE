# Operator: disconnect Wi-Fi and Ethernet before running; reconnect after the result is saved.
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $repoRoot
$run = Get-Content -Raw tests/results/logs/readiness-run.json | ConvertFrom-Json
if ($run.project -notmatch '^sih-readiness-[a-z0-9-]+$') { throw 'Use the isolated readiness stack.' }
$dest = Join-Path $run.directory ('physical-offline-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $dest | Out-Null
$result = @{passed=$false;physical_offline=$false;commit=(& git rev-parse HEAD);started=(Get-Date -Format o)}
function Disconnected-Adapters {
    $adapters = @(Get-NetAdapter -Physical | Select-Object Name,Status,InterfaceDescription)
    if (-not $adapters.Count -or @($adapters | Where-Object Status -eq 'Up').Count) {
        throw 'Physical network disconnection is not established. Disconnect Wi-Fi/Ethernet first.'
    }
    return $adapters
}
try {
    $result.adapters_before = @(Disconnected-Adapters)
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1 -Action Stop -Audit *> (Join-Path $dest 'stop.log')
    if ($LASTEXITCODE -ne 0) { throw 'Isolated shutdown failed.' }
    $started = Get-Date
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1 -Action Start -Audit *> (Join-Path $dest 'start.log')
    if ($LASTEXITCODE -ne 0) { throw 'Disconnected cold startup failed.' }
    $result.cold_start_seconds = ((Get-Date) - $started).TotalSeconds
    $env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:5174'
    $env:AUDIT_ARTIFACT_DIR = $dest
    Push-Location frontend
    try {
        & npx.cmd --no-install playwright test coordination-workflow.spec.ts workflow.spec.ts readiness.spec.ts *> (Join-Path $dest 'browser.log')
        if ($LASTEXITCODE -ne 0) { throw 'Disconnected workflow regression failed.' }
    } finally { Pop-Location }
    $result.adapters_after = @(Disconnected-Adapters)
    $result.physical_offline = $true
    $result.passed = $true
} catch {
    $result.error = $_.Exception.Message
    throw
} finally {
    $result.finished = Get-Date -Format o
    $result | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 (Join-Path $dest 'result.json')
    Write-Host "Evidence saved in $dest. You may reconnect now."
}
