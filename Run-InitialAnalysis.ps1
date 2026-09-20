param([Parameter(Mandatory=$true)][string]$GameDirectory)
$ErrorActionPreference = 'Stop'
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $bundledPython) {
    $probePython = $bundledPython
} else {
    $probePython = (Get-Command python -ErrorAction Stop).Source
}
& $probePython -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 or newer is required.' }
$reportDirectory = Join-Path $PSScriptRoot ('reports\initial-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
& $probePython (Join-Path $PSScriptRoot 'tools\local_probe\scan_game.py') $GameDirectory --output $reportDirectory
if ($LASTEXITCODE -ne 0) { throw "Inventory incomplete. Inspect $reportDirectory for diagnostics." }
Write-Output "Analysis report: $reportDirectory"
