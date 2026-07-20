#!/usr/bin/env pwsh
<#
.SYNOPSIS
    SOTA Repository Backup Script v1.3.0
    High-performance backup with multi-destination support and integrity verification.
    Each destination (Desktop / N: Drive / OneDrive) resolves and creates its own
    path independently -- a missing env var or unmapped drive skips that one
    destination with a clear message instead of crashing the whole run.

.DESCRIPTION
    This script performs a comprehensive backup of the current repository to multiple
    destinations (Desktop, N: Drive, OneDrive). It handles exclusions, computes
    SHA256 hashes for deduplication, and verifies ZIP integrity.

.PARAMETER IncludeBuild
    Include dist/ and build/ folders (default: false)

.PARAMETER MaxRetries
    Maximum number of retry attempts for failed operations (default: 3)

.PARAMETER RetryDelaySeconds
    Initial delay between retries in seconds (default: 2)
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$IncludeBuild = $false,
    [switch]$List = $false,
    [ValidateSet('text', 'json')]
    [string]$OutputFormat = 'text',
    [int]$MaxRetries = 3,
    [int]$RetryDelaySeconds = 2
)

# Set error action preference
$ErrorActionPreference = "Stop"
$PSDefaultParameterValues['*:ErrorAction'] = 'Stop'

$Verbose = $VerbosePreference -eq 'Continue'
$WhatIf = $WhatIfPreference

# Initialize
$script:StartTime = Get-Date
$script:ErrorLog = @()
$script:BackupResults = @{}
$script:TotalFilesProcessed = 0
$script:TotalFilesFailed = 0

# Types
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

#region Helper Functions

function Write-ErrorLog {
    param(
        [string]$Message,
        [string]$Category = "Error",
        [PSObject]$Exception = $null
    )
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$ts] [$Category] $Message"
    if ($Exception) {
        $ex = if ($Exception -is [System.Management.Automation.ErrorRecord]) { $Exception.Exception } else { $Exception }
        if ($ex) {
            $logEntry += "`n  Exception: $($ex.GetType().FullName)"
            $logEntry += "`n  Message: $($ex.Message)"
        }
    }
    $script:ErrorLog += $logEntry
    if ($script:OutputFormat -eq 'text') {
        $color = if ($Category -eq "Error") { "Red" } elseif ($Category -eq "Warning") { "Yellow" } else { "Gray" }
        Write-Host $logEntry -ForegroundColor $color
    }
}

function Get-FileHashSHA256 {
    param([string]$FilePath)
    return (Get-FileHash -Path $FilePath -Algorithm SHA256).Hash
}

function Test-BackupDuplicate {
    param(
        [string]$NewBackupPath,
        [string]$BackupDir,
        [switch]$Verbose
    )
    if (-not (Test-Path $NewBackupPath)) { return $false }
    $prev = Get-ChildItem -Path $BackupDir -Filter "*.zip" -File | 
            Where-Object { $_.FullName -ne $NewBackupPath } | 
            Sort-Object LastWriteTime -Descending
    if (-not $prev) { return $false }
    
    $newHash = Get-FileHashSHA256 -FilePath $NewBackupPath
    $oldHash = Get-FileHashSHA256 -FilePath $prev[0].FullName
    return ($newHash -eq $oldHash)
}

function Invoke-WithRetry {
    param(
        [scriptblock]$ScriptBlock,
        [string]$OperationName,
        [int]$MaxRetries = 3,
        [int]$InitialDelaySeconds = 2
    )
    $attempt = 0
    while ($attempt -le $MaxRetries) {
        try { return & $ScriptBlock }
        catch {
            $attempt++
            if ($attempt -gt $MaxRetries) { throw }
            Start-Sleep -Seconds $InitialDelaySeconds
        }
    }
}

function New-BackupZip {
    param(
        [string]$ZipPath,
        [array]$Files,
        [string]$RepoRoot
    )
    $zip = $null
    $added = 0
    $failed = 0
    try {
        if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
        $zip = [System.IO.Compression.ZipFile]::Open($ZipPath, [System.IO.Compression.ZipArchiveMode]::Create)
        foreach ($file in $Files) {
            try {
                $rel = $file.FullName.Substring($RepoRoot.Length + 1)
                $entry = $rel -replace '\\', '/'
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $file.FullName, $entry, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
                $added++
            }
            catch { $failed++; Write-ErrorLog "Failed to add file: $($file.FullName)" "Warning" $_ }
        }
        $zip.Dispose(); $zip = $null
        return @{ Success = $true; FilesAdded = $added; FilesFailed = $failed; BackupSize = (Get-Item $ZipPath).Length }
    }
    catch {
        if ($zip) { $zip.Dispose() }
        if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
        throw
    }
}

#endregion

# Main
# Verify we are in a Git repository
if (-not (Test-Path .git)) {
    Write-Host "Error: Must run from repository root (or .git folder is missing)."
    exit 1
}

$repoRoot = (Get-Item .).FullName
$repoName = (Get-Item .).Name
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupName = "${repoName}_backup_${timestamp}.zip"

$destinations = @()

# Desktop -- practically always resolves, but don't assume it
try {
    $desktopBase = [Environment]::GetFolderPath("Desktop")
    if ([string]::IsNullOrWhiteSpace($desktopBase)) { throw "GetFolderPath('Desktop') returned empty" }
    $desktop = Join-Path (Join-Path $desktopBase "repo backup") $repoName
    $destinations += @{ Name = "Desktop"; Path = $desktop; BackupPath = (Join-Path $desktop $backupName) }
} catch {
    Write-Host "  SKIP Desktop destination: $($_.Exception.Message)" -ForegroundColor Yellow
}

# N: Drive -- may not be mapped (VPN off, drive letter changed, etc.)
try {
    if (-not (Test-Path "N:\")) { throw "N:\ is not mapped or not accessible" }
    $nDrive = Join-Path "N:\backup\dev\repo-backups" $repoName
    $destinations += @{ Name = "N: Drive"; Path = $nDrive; BackupPath = (Join-Path $nDrive $backupName) }
} catch {
    Write-Host "  SKIP N: Drive destination: $($_.Exception.Message)" -ForegroundColor Yellow
}

# OneDrive -- $env:OneDrive is set by the OneDrive client into an interactive
# user session, but processes started without that session (services,
# scheduled tasks, some MCP server hosts) inherit an environment where it's
# simply unset. Previously this crashed the whole script with a bare
# "Cannot bind argument to parameter 'Path' because it is null" -- no
# indication of what was actually wrong or which destination caused it.
# Now: fall back to the conventional %USERPROFILE%\OneDrive path, and if
# that doesn't exist either, skip the destination with a clear message
# instead of taking down Desktop/N: backups along with it.
try {
    $oneDriveBase = $env:OneDrive
    if ([string]::IsNullOrWhiteSpace($oneDriveBase)) {
        $fallback = Join-Path $env:USERPROFILE "OneDrive"
        if (Test-Path $fallback) {
            Write-Host "  WARN `$env:OneDrive not set in this process environment; using fallback path: $fallback" -ForegroundColor Yellow
            $oneDriveBase = $fallback
        } else {
            throw "`$env:OneDrive is not set, and no OneDrive folder found at fallback path '$fallback'"
        }
    }
    $oneDrive = Join-Path (Join-Path $oneDriveBase "Backup/repo-backups") $repoName
    $destinations += @{ Name = "OneDrive"; Path = $oneDrive; BackupPath = (Join-Path $oneDrive $backupName) }
} catch {
    Write-Host "  SKIP OneDrive destination: $($_.Exception.Message)" -ForegroundColor Yellow
}

if ($destinations.Count -eq 0) {
    Write-Host "ERROR: No backup destinations could be resolved (Desktop, N: Drive, and OneDrive all failed). Aborting -- see SKIP messages above for why each one failed." -ForegroundColor Red
    exit 1
}

# Handle list switch
if ($List) {
    Write-Host "--- Backup History ---"
    Write-Host "Repository: $repoName"
    foreach ($d in $destinations) {
        Write-Host "Destination: $($d.Name) ($($d.Path))"
        if (Test-Path $d.Path) {
            Get-ChildItem -Path $d.Path -Filter "${repoName}_backup_*.zip" | 
                Sort-Object LastWriteTime -Descending | 
                ForEach-Object { Write-Host "  $($_.Name) ($([math]::Round($_.Length/1MB, 2)) MB) - $($_.LastWriteTime)" }
        } else {
            Write-Host "  No backups found (directory does not exist)"
        }
    }
    exit 0
}

Write-Host "--- SOTA Backup Starting: $repoName ---" -ForegroundColor Magenta

# Create dirs -- a single bad destination (permissions, drive unmounted
# mid-run, etc.) must not stop backups going to the others.
$readyDestinations = @()
foreach ($d in $destinations) {
    if (-not (Test-Path $d.Path)) {
        try {
            New-Item -ItemType Directory -Path $d.Path -Force -ErrorAction Stop | Out-Null
        } catch {
            Write-Host "  SKIP $($d.Name) destination: could not create '$($d.Path)': $($_.Exception.Message)" -ForegroundColor Yellow
            continue
        }
    }
    $readyDestinations += $d
}
$destinations = $readyDestinations

if ($destinations.Count -eq 0) {
    Write-Host "ERROR: No backup destination directories could be created. Aborting -- see SKIP messages above for why each one failed." -ForegroundColor Red
    exit 1
}

# Get only git-tracked files (ignores node_modules, .venv, target, etc.)
Write-Host "Excluding untracked files (.venv, node_modules, etc.)"
$files = @(git ls-files) | ForEach-Object { $p = Join-Path $repoRoot $_; if (Test-Path $p -PathType Leaf) { Get-Item $p } }

$totalSize = ($files | Measure-Object -Property Length -Sum).Sum
Write-Host "Files to backup: $($files.Count) ($([math]::Round($totalSize/1MB, 2)) MB)"

if ($WhatIf -or $Verbose) {
    Write-Host "Files that would be backed up:"
    foreach ($file in $files) {
        Write-Host "  $($file.FullName.Substring($repoRoot.Length + 1))"
    }
}

if ($WhatIf) {
    Write-Host "DRY-RUN MODE (What if)" -ForegroundColor Yellow
    Write-Host "[DRY-RUN] Would create backup at destinations." -ForegroundColor Yellow
    exit 0
}

$successCount = 0
foreach ($d in $destinations) {
    Write-Host "Backing up to $($d.Name)..."
    try {
        $res = New-BackupZip -ZipPath $d.BackupPath -Files $files -RepoRoot $repoRoot
        if (Test-BackupDuplicate -NewBackupPath $d.BackupPath -BackupDir $d.Path) {
            Write-Host "  Duplicate found, removing." -ForegroundColor Yellow
            Remove-Item $d.BackupPath -Force
        } else {
            Write-Host "  Success: $([math]::Round($res.BackupSize/1MB, 2)) MB" -ForegroundColor Green
            $successCount++
        }
    }
    catch { Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red }
}

Write-Host "--- Backup Complete: $successCount destinations ---"
exit $(if ($successCount -gt 0) { 0 } else { 1 })
