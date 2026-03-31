#Requires -Version 5.1
<#
.SYNOPSIS
    Starts the LeetCode Interview Browser in a Podman container.
.DESCRIPTION
    Checks that Podman is available, auto-builds the image if missing,
    then runs the container and opens http://localhost:8000.
#>

$ErrorActionPreference = "Stop"

$ImageName   = "leetcode-browser"
$HostPort    = 8000
$ProjectRoot = $PSScriptRoot
$Url         = "http://localhost:$HostPort"

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "  +------------------------------------------+" -ForegroundColor Yellow
Write-Host "  |   LeetCode Interview Browser             |" -ForegroundColor Yellow
Write-Host "  +------------------------------------------+" -ForegroundColor Yellow
Write-Host ""

# ---------------------------------------------------------------------------
# Check Podman
# ---------------------------------------------------------------------------
if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    Write-Host "  [ERROR] podman not found in PATH." -ForegroundColor Red
    Write-Host "          Install Podman Desktop from https://podman-desktop.io" -ForegroundColor Gray
    Write-Host ""
    Read-Host "  Press Enter to exit"
    exit 1
}

$podmanVersion = & podman --version 2>&1
Write-Host "  Podman : $podmanVersion" -ForegroundColor DarkGray

# ---------------------------------------------------------------------------
# Build image if it does not exist
# ---------------------------------------------------------------------------
$existingImage = & podman images --quiet $ImageName 2>$null
if (-not $existingImage) {
    Write-Host ""
    Write-Host "  Image '$ImageName' not found - building now..." -ForegroundColor Yellow
    Write-Host "  (Imports all company CSVs into SQLite. Takes ~30-60 seconds.)" -ForegroundColor DarkGray
    Write-Host ""
    & podman build -t $ImageName $ProjectRoot
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "  [ERROR] Build failed. Check the output above." -ForegroundColor Red
        Write-Host ""
        Read-Host "  Press Enter to exit"
        exit 1
    }
    Write-Host ""
    Write-Host "  Build complete." -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# Start container
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "  Starting container on port $HostPort ..." -ForegroundColor Cyan
Write-Host "  URL  : $Url" -ForegroundColor Green
Write-Host "  Stop : Ctrl+C" -ForegroundColor DarkGray
Write-Host ""

Start-Sleep -Milliseconds 800
Start-Process $Url

try {
    & podman run --rm -p "${HostPort}:8000" $ImageName
}
finally {
    Write-Host ""
    Write-Host "  Container stopped." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "  Press Enter to close"
}
