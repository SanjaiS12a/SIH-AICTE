param(
    [ValidateSet('Start','Stop','Prepare','Check')][string]$Action = 'Start',
    [switch]$Audit,
    [switch]$Demo,
    [switch]$Prepare
)
$ErrorActionPreference = 'Stop'
if ($Demo -and -not $Audit) { throw '-Demo requires -Audit; the working database cannot be used for demo activation.' }
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if ($Demo) {
    $names=@('DEMO_MODE','ENABLE_REVIEWED_FACTS','ENABLE_INCIDENT_GROUPS','AUDIT_RESULTS','API_PROXY_TARGET')
    $previous=@{}
    foreach ($name in $names) { $previous[$name]=[Environment]::GetEnvironmentVariable($name,'Process') }
    try {
        $env:DEMO_MODE='1'; $env:ENABLE_REVIEWED_FACTS='1'; $env:ENABLE_INCIDENT_GROUPS='1'
        $metadata=Join-Path $repoRoot 'tests/results/logs/readiness-run.json'
        if (-not (Test-Path -LiteralPath $metadata)) {
            if ($Action -eq 'Stop') { throw 'No isolated demo profile exists. Prepare the demo first.' }
            $sha=[Security.Cryptography.SHA256]::Create()
            try { $key=[BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($repoRoot))).Replace('-','').Substring(0,8).ToLowerInvariant() } finally { $sha.Dispose() }
            $destination=Join-Path $repoRoot ('tests/results/runs/demo-'+[guid]::NewGuid().ToString('N'))
            New-Item -ItemType Directory -Path $destination | Out-Null
            New-Item -ItemType Directory -Force -Path (Split-Path $metadata) | Out-Null
            $bytes=[Text.Encoding]::UTF8.GetBytes((@{project="sih-readiness-demo-$key";directory=$destination} | ConvertTo-Json))
            $file=[IO.File]::Open($metadata,[IO.FileMode]::CreateNew)
            try { $file.Write($bytes,0,$bytes.Length) } finally { $file.Dispose() }
        }
        & $PSCommandPath -Audit -Action $Action -Prepare:$Prepare
        if ($LASTEXITCODE -ne 0) { throw "Demo controller failed with exit code $LASTEXITCODE." }
    } finally {
        foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$previous[$name],'Process') }
    }
    return
}
Set-Location -LiteralPath $repoRoot
if ($Prepare) { $Action = 'Prepare' }
$runRoot = Join-Path $repoRoot '.run'
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
$frontendPort = 5173
$apiPort = 8000
$composeArgs = @('compose')
if ($Audit) {
    $runFile = Join-Path $repoRoot 'tests/results/logs/readiness-run.json'
    if (-not (Test-Path -LiteralPath $runFile)) { throw 'Create the isolated audit run before using -Audit.' }
    $auditRun = Get-Content -Raw -LiteralPath $runFile | ConvertFrom-Json
    if ($auditRun.project -notmatch '^sih-readiness-[a-z0-9-]+$') { throw 'Invalid audit project name.' }
    $env:AUDIT_RESULTS = $auditRun.directory
    $composeArgs += @('-p', $auditRun.project, '-f', 'compose.audit.yaml')
    $frontendPort = 5174
    $apiPort = 8001
}
$pidFile = Join-Path $runRoot ("frontend-$frontendPort.json")
function Invoke-Compose {
    & docker @composeArgs @args
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed: $($args -join ' ')" }
}
function Verify-Assets {
    $expected = Get-Content -Raw backend/model-manifest.json | ConvertFrom-Json
    $actual = Get-Content -Raw models/minilm/revision.json | ConvertFrom-Json
    $calibration = Get-Content -Raw backend/calibration.json | ConvertFrom-Json
    if ($actual.revision -ne $expected.revision -or $calibration.model_revision -ne $expected.revision) { throw 'Model revision does not match the frozen baseline.' }
    foreach ($asset in @('models/minilm/tokenizer.json','models/minilm/config.json','models/minilm/1_Pooling/config.json','backend/licenses/minilm-LICENSE.txt')) {
        if (-not (Test-Path -LiteralPath $asset)) { throw "Missing prepared asset: $asset" }
    }
    $stream = [IO.File]::OpenRead((Join-Path $repoRoot 'models/minilm/model.safetensors'))
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $hash = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $sha.Dispose() }
    if ($hash -ne $expected.weights_sha256) { throw 'Model weights checksum mismatch.' }
}
function Wait-Endpoint([string]$Url) {
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) { return }
        } catch { }
        Start-Sleep -Seconds 1
    }
    throw "Service did not become ready: $Url"
}
function Wait-Database {
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        $container = & docker @composeArgs ps -q db
        if ($LASTEXITCODE -eq 0 -and $container) {
            $health = & docker inspect --format '{{.State.Health.Status}}' $container
            if ($LASTEXITCODE -eq 0 -and $health -eq 'healthy') { return }
        }
        Start-Sleep -Seconds 1
    }
    throw 'Database did not pass its health check.'
}
function Wait-Worker {
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        $container = & docker @composeArgs ps -q worker
        if ($LASTEXITCODE -ne 0 -or -not $container) { throw 'Worker container was not created.' }
        $state = & docker inspect --format '{{json .State}}' $container | ConvertFrom-Json
        if ($LASTEXITCODE -ne 0 -or -not $state.Running) { throw 'Worker exited before becoming ready. Inspect the worker logs.' }
        $previousPreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue' # Windows PowerShell treats native stderr log lines as ErrorRecords.
            $logs = & docker logs --since $state.StartedAt $container 2>&1 | Out-String
            $logsStatus = $LASTEXITCODE
        } finally { $ErrorActionPreference = $previousPreference }
        if ($logsStatus -eq 0 -and $logs -match 'ready for work' -and $logs -match 'Q Cluster .+ running\.') { return }
        Start-Sleep -Seconds 1
    }
    throw 'Worker cluster did not report readiness. Inspect the worker logs.'
}
function Stop-OwnedFrontend {
    if (-not (Test-Path -LiteralPath $pidFile)) { return }
    $state = Get-Content -Raw -LiteralPath $pidFile | ConvertFrom-Json
    $owned = Get-CimInstance Win32_Process -Filter "ProcessId=$([int]$state.pid)" -ErrorAction SilentlyContinue
    if ($owned) {
        if ($owned.CommandLine.IndexOf($repoRoot, [StringComparison]::OrdinalIgnoreCase) -lt 0 -or $owned.CommandLine -notmatch 'vite.*preview' -or $owned.CreationDate.ToUniversalTime().Ticks.ToString() -ne $state.created) { throw 'Saved PID is no longer owned by this portal; refusing to stop it.' }
        Stop-Process -Id $owned.ProcessId
    }
    Remove-Item -LiteralPath $pidFile
}
function Assert-DependenciesIdle {
    $active=Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object {
        $_.CommandLine -and $_.CommandLine.IndexOf($repoRoot,[StringComparison]::OrdinalIgnoreCase) -ge 0 -and $_.CommandLine -match 'vite[\\/]bin[\\/]vite\.js'
    }
    if ($active) { throw 'Stop other workspace Vite previews/builds before preparation; their Windows executable locks prevent npm ci.' }
}
if ($Action -eq 'Stop') {
    Stop-OwnedFrontend
    Invoke-Compose stop api worker db
    Write-Host 'Portal services stopped; database volumes preserved.'
    exit 0
}
$nodeText = & node --version
if ($LASTEXITCODE -ne 0) { throw 'Node.js is not available.' }
$nodeVersion = [version]$nodeText.Trim().TrimStart('v')
if (-not ($nodeVersion.Major -gt 22 -or ($nodeVersion.Major -eq 22 -and $nodeVersion.Minor -ge 12) -or ($nodeVersion.Major -eq 20 -and $nodeVersion.Minor -ge 19))) { throw 'Use Node 20.19+, 22.12+, or the verified Node 24 installation.' }
& docker info --format '{{.ServerVersion}}' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop, then retry.' }
if ($Action -eq 'Prepare') {
    Stop-OwnedFrontend
    Assert-DependenciesIdle
    if (-not $Audit -and -not (Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
    if (-not $Audit) { Invoke-Compose build }
    if ($Audit -and $env:DEMO_MODE -eq '1') {
        $previousPreference=$ErrorActionPreference
        try { $ErrorActionPreference='Continue'; & docker image inspect aicte-coordination:local *> $null; $imageStatus=$LASTEXITCODE }
        finally { $ErrorActionPreference=$previousPreference }
        if ($imageStatus -ne 0) {
            New-Item -ItemType Directory -Force -Path (Join-Path $repoRoot 'backend/.wheels') | Out-Null
            & docker build -t aicte-coordination:local (Join-Path $repoRoot 'backend')
            if ($LASTEXITCODE -ne 0) { throw 'Isolated demo image preparation failed.' }
        }
    }
    Invoke-Compose up -d db
    Wait-Database
    Invoke-Compose run --rm --no-deps api python manage.py migrate --noinput
    if ($Audit) {
        if ($env:DEMO_MODE -eq '1' -and -not (Test-Path -LiteralPath 'models/minilm/model.safetensors')) {
            $modelDirectory=Join-Path $repoRoot 'models'
            New-Item -ItemType Directory -Force -Path $modelDirectory | Out-Null
            Invoke-Compose run --rm --no-deps -v ($modelDirectory.Replace('\','/')+':/models:rw') -e HF_HUB_OFFLINE=0 -e TRANSFORMERS_OFFLINE=0 api python manage.py download_model
        }
        Verify-Assets
    } else { Invoke-Compose run --rm --no-deps -e HF_HUB_OFFLINE=0 -e TRANSFORMERS_OFFLINE=0 api python manage.py download_model }
    # Preparation seeds only an empty designated database; existing data is never augmented.
    Invoke-Compose run --rm --no-deps api python manage.py seed_if_empty
    Push-Location frontend
    try {
        & npm.cmd ci
        if ($LASTEXITCODE -ne 0) { throw 'Locked dependency installation failed.' }
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
    Write-Host 'Preparation complete. Use -Action Start for prepared startup.'
    exit 0
}
Verify-Assets
if (-not (Test-Path -LiteralPath 'frontend/dist/index.html')) { throw 'Frontend bundle missing. Run -Action Prepare while online.' }
if (-not $Audit -and -not (Test-Path -LiteralPath '.env')) { throw 'Environment configuration missing. Run -Action Prepare.' }
if ($Action -eq 'Check') { Write-Host 'Runtime prerequisites and pinned assets verified.'; exit 0 }
$existing = Get-NetTCPConnection -LocalPort $frontendPort -State Listen -ErrorAction SilentlyContinue
if ($existing) { throw "Port $frontendPort is occupied. Stop the existing portal or unrelated process explicitly." }
Invoke-Compose up -d --pull never --no-build db
Wait-Database
Invoke-Compose run --rm --no-deps api python manage.py migrate --noinput
Invoke-Compose up -d --pull never --no-build api worker
Wait-Worker
Wait-Endpoint "http://127.0.0.1:$apiPort/api/session"
$env:API_PROXY_TARGET = "http://127.0.0.1:$apiPort"
$nodePath = (Get-Command node).Source
$vitePath = Join-Path $repoRoot 'frontend/node_modules/vite/bin/vite.js'
$stdinPath = Join-Path $runRoot "frontend-$frontendPort-stdin.txt"
[IO.File]::WriteAllText($stdinPath, '')
$child = Start-Process -FilePath $nodePath -ArgumentList @(('"' + $vitePath + '"'),'preview','--host','127.0.0.1','--port',"$frontendPort",'--strictPort') -WorkingDirectory (Join-Path $repoRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardInput $stdinPath -RedirectStandardOutput (Join-Path $runRoot "frontend-$frontendPort.log") -RedirectStandardError (Join-Path $runRoot "frontend-$frontendPort-error.log")
$owned = Get-CimInstance Win32_Process -Filter "ProcessId=$($child.Id)"
@{pid=$child.Id;created=$owned.CreationDate.ToUniversalTime().Ticks.ToString()} | ConvertTo-Json | Set-Content -LiteralPath $pidFile
try { Wait-Endpoint "http://127.0.0.1:$frontendPort/api/session" } catch { Stop-OwnedFrontend; throw }
Write-Host "Portal ready at http://127.0.0.1:$frontendPort (API and worker initialization verified; pinned local assets)."
Write-Host 'Account credentials come from the configured database; DEMO_PASSWORD is used only when seeding new accounts.'
