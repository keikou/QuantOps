$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "pytest failed." }
