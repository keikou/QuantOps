$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot
Write-Host "Running nightly alpha weight update..." -ForegroundColor Cyan
python -m ai_hedge_bot.scheduler.nightly_weight_update
if ($LASTEXITCODE -ne 0) {
    Write-Host "Nightly update failed." -ForegroundColor Red
    exit 1
}
Write-Host "Nightly update complete." -ForegroundColor Green
