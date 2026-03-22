param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [switch]$SkipPytest
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot

function Step($name) {
    Write-Host ""
    Write-Host "=== $name ===" -ForegroundColor Cyan
}

function Assert($condition, $message) {
    if (-not $condition) { throw $message }
}

function Get-Json($url) {
    return Invoke-RestMethod -Method GET -Uri $url
}

function Post-Json($url) {
    return Invoke-RestMethod -Method POST -Uri $url
}

if (Test-Path ".\.venv\Scripts\python.exe") {
    $PythonCmd = ".\.venv\Scripts\python.exe"
} else {
    $PythonCmd = "python"
}

if (-not $SkipPytest) {
    Step "pytest"
    & $PythonCmd -m pytest tests/test_phaseg_api.py tests/test_phaseg_sprint1_api.py tests/test_phaseg_sprint2_api.py tests/test_phaseg_sprint3_api.py tests/test_api.py -q
    if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
}

Step "API health"
$health = Get-Json "$BaseUrl/system/health"
Assert ($health.status -eq 'ok') "/system/health failed"

Step "Generate signals"
$signals = Post-Json "$BaseUrl/signals/generate"
Assert ($signals.status -eq 'ok') "/signals/generate failed"
Assert ($signals.count -ge 1) "signals count is 0"

Step "Prepare portfolio"
$portfolio = Post-Json "$BaseUrl/portfolio/prepare"
Assert ($portfolio.status -eq 'ok') "/portfolio/prepare failed"
Assert ($portfolio.decisions.Count -ge 1) "portfolio decisions empty"

Step "Shadow cycle"
$shadow = Post-Json "$BaseUrl/orchestrator/shadow/run-cycle"
Assert ($shadow.status -eq 'ok') "/orchestrator/shadow/run-cycle failed"

Step "Execution quality latest"
$eqLatest = Get-Json "$BaseUrl/execution/quality/latest"
Assert ($null -ne $eqLatest.fill_rate) "execution/quality/latest fill_rate is null"
Assert ($null -ne $eqLatest.avg_slippage_bps) "execution/quality/latest avg_slippage_bps is null"

Step "Analytics"
$signalSummary = Get-Json "$BaseUrl/analytics/signal-summary"
Assert ($signalSummary.signals_evaluated -ge 1) "signals_evaluated < 1"
Assert ($signalSummary.signal_count -ge 1) "signal_count < 1"

$portfolioSummary = Get-Json "$BaseUrl/analytics/portfolio-summary"
Assert ($portfolioSummary.portfolio_count -ge 1) "portfolio_count < 1"

$shadowSummary = Get-Json "$BaseUrl/analytics/shadow-summary"
Assert ($shadowSummary.shadow_cycles -ge 1) "shadow_cycles < 1"
Assert ($shadowSummary.shadow_order_count -ge 1) "shadow_order_count < 1"
Assert ($shadowSummary.shadow_fill_count -ge 1) "shadow_fill_count < 1"

$executionSummary = Get-Json "$BaseUrl/analytics/execution-quality"
Assert ($null -ne $executionSummary.fill_rate) "analytics/execution-quality fill_rate is null"
Assert ($null -ne $executionSummary.avg_slippage_bps) "analytics/execution-quality avg_slippage_bps is null"

Step "Dashboard"
$global = Get-Json "$BaseUrl/dashboard/global"
Assert ($global.cards.signal_count -ge 1) "dashboard/global signal_count < 1"
Assert ($global.cards.portfolio_count -ge 1) "dashboard/global portfolio_count < 1"
Assert ($null -ne $global.cards.fill_rate) "dashboard/global fill_rate is null"

Step "OpenAPI"
$openapi = Get-Json "$BaseUrl/openapi.json"
Assert ($openapi.paths.PSObject.Properties.Name -contains '/analytics/signal-summary') "OpenAPI missing /analytics/signal-summary"
Assert ($openapi.paths.PSObject.Properties.Name -contains '/dashboard/global') "OpenAPI missing /dashboard/global"

Step "DuckDB inspection"
powershell -ExecutionPolicy Bypass -File "$scriptDir/check_phaseg_duckdb.ps1"
if ($LASTEXITCODE -ne 0) { throw "DuckDB inspection failed" }

Write-Host ""
Write-Host "run_all_checks.ps1 completed successfully" -ForegroundColor Green
