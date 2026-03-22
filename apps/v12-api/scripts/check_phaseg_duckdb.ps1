param(
    [string]$DbPath = ""
)
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot
$pythonCmd = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
if ($DbPath -ne "") {
    & $pythonCmd .\scripts\inspect_phaseg_duckdb.py $DbPath
} else {
    & $pythonCmd .\scripts\inspect_phaseg_duckdb.py
}
exit $LASTEXITCODE
