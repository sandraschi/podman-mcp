param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)
$child = Join-Path $PSScriptRoot "web_sota/start.ps1"
if (-not (Test-Path -LiteralPath $child)) {
    Write-Error "Missing launcher: $child"
    exit 1
}
& $child @PSBoundParameters
exit $LASTEXITCODE

