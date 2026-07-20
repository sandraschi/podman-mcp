# Script to create a new markdown file with proper formatting
param(
    [Parameter(Mandatory=$true)]
    [string]$Path,
    [string]$Title = "New Document"
)

# Get the directory of the current script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$templatePath = Join-Path $scriptDir "..\.vscode\markdown-template.md"

# Create directory if it doesn't exist
$directory = Split-Path -Parent $Path
if (!(Test-Path $directory)) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

# Get current date in ISO format
$date = Get-Date -Format "yyyy-MM-dd"

# Read template and replace placeholders
$content = Get-Content -Path $templatePath -Raw
$content = $content -replace "# Title", "# $Title"
$content = $content -replace "\{\{date\}\}", $date

# Write to new file with UTF-8 without BOM
$content = $content.TrimEnd() + "`n"  # Ensure exactly one newline at end
[System.IO.File]::WriteAllText($Path, $content, [System.Text.UTF8Encoding]::new($false))

Write-Host "Created new markdown file: $Path"

# Open the file in VS Code if available
if (Get-Command code -ErrorAction SilentlyContinue) {
    code $Path
}
