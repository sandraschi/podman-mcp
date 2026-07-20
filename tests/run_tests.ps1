# Test runner script for PodmanMCP tests
# Run with: .\run_tests.ps1 [test_module]

param(
    [string]$TestModule = ""  # Optional: specific test module to run
)

# Create test output directory if it doesn't exist
$testOutputDir = "test_output"
if (-not (Test-Path -Path $testOutputDir)) {
    New-Item -ItemType Directory -Path $testOutputDir | Out-Null
}

# Generate timestamp for unique output file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputFile = "$testOutputDir\test_output_${timestamp}.log"

# Build test command
$testCommand = "pytest -v"
if ($TestModule) {
    $testCommand += " tests/${TestModule}.py"
} else {
    $testCommand += " tests/"
}

# Add logging of command to output
"# Test Run: $(Get-Date)" | Out-File -FilePath $outputFile -Encoding utf8
"# Command: $testCommand" | Out-File -FilePath $outputFile -Encoding utf8 -Append
"`n" | Out-File -FilePath $outputFile -Encoding utf8 -Append

# Run tests and capture output
Write-Host "Running tests... (Output will be saved to tests\$outputFile)"
Invoke-Expression "$testCommand 2>&1" | Tee-Object -FilePath $outputFile -Append

# Show test results
Write-Host "`nTest execution complete. Output saved to: tests\$outputFile"
Write-Host "Last 10 lines of output:"
Get-Content -Path $outputFile -Tail 10
