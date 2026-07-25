param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser,
    [switch]$ReuseIfRunning)

$WebPort = 11112
$BackendPort = 11113
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly

$portResolve = @{
    Ports      = @($WebPort, $BackendPort)
    Label      = "podman-mcp"
    AllowReuse = $ReuseIfRunning
}
if ($ReuseIfRunning) {
    $portResolve.HealthChecks = @{
        $WebPort = "http://127.0.0.1:$WebPort/"
        $BackendPort = "http://127.0.0.1:$BackendPort/api/health"
    }
}
$portState = Resolve-FleetPortConflict @portResolve
if ($portState.Action -eq 'Blocked') { exit 1 }
if ($portState.Reuse) { return }

# 2. Setup
Set-Location $PSScriptRoot
if (-not (Test-Path "node_modules")) { npm install }

# 3. Start the Python backend (Background)
Write-Host "Starting Python backend on port $BackendPort ..." -ForegroundColor Cyan

$srcPath = Join-Path $ProjectRoot "src"
$backendCmd = "`$env:PYTHONPATH = '$srcPath;$PSScriptRoot'; Set-Location '$PSScriptRoot'; uv run uvicorn customization.server:app --host 127.0.0.1 --port $BackendPort --log-level info"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# 4. Wait for backend to be ready (avoid ECONNREFUSED on /api/*)
$healthUrl = "http://127.0.0.1:$BackendPort/api/health"
$maxAttempts = 40
$attempt = 0
$backendReady = $false
do {
    $attempt++
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch { }
    if ($attempt -ge $maxAttempts) {
        Write-Host "Backend did not respond after ${maxAttempts}s (uvicorn may have failed - check the backend PowerShell window)." -ForegroundColor Red
        break
    }
    Write-Host "  Waiting for backend... ($attempt/$maxAttempts)" -ForegroundColor Gray
} while ($true)

if (-not $backendReady) {
    Write-Host "Aborting: /api/dashboard needs the backend on port $BackendPort." -ForegroundColor Red
    exit 1
}

Write-Host "Backend ready." -ForegroundColor Green

if (-not $FleetStart.RunFrontend) { return }

# 5. Run server (Vite dev)
if (-not $FleetStart.RunFrontend) { return }

Write-Host "Starting Vite frontend on port $WebPort ..." -ForegroundColor Green

# 4b. Launch background task to open browser once frontend is ready (Auto-opened by Antigravity)
$frontendUrl = "http://127.0.0.1:$WebPort/"
$pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
if (-not $FleetStart.RunFrontend) { return }
npm run dev -- --port $WebPort --host







