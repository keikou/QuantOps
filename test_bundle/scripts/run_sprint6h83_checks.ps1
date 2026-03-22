$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")
Set-Location $RepoRoot

Write-Host "=== Sprint6H-8.3 checks ==="

Write-Host "[1/4] Python compile"
python -m py_compile `
  apps/v12-api/ai_hedge_bot/api/routes/runtime.py `
  apps/v12-api/ai_hedge_bot/api/routes/execution.py `
  apps/v12-api/ai_hedge_bot/services/runtime/runtime_service.py `
  apps/quantops-api/app/api/routes/scheduler.py `
  apps/quantops-api/app/api/routes/execution.py `
  apps/quantops-api/app/api/routes/analytics.py `
  apps/quantops-api/app/services/command_center_service.py `
  apps/quantops-api/app/services/execution_service.py `
  apps/quantops-api/app/services/analytics_service.py `
  apps/quantops-api/app/clients/v12_client.py

Write-Host "[2/4] V12 focused tests"
Push-Location apps/v12-api
python -m pytest tests/test_sprint6h8_risk_execution_stop.py tests/test_sprint6h8_2_scheduler_and_state.py -q
Pop-Location

Write-Host "[3/4] QuantOps focused tests (isolated DB)"
$env:QUANTOPS_DB_PATH = Join-Path $RepoRoot "runtime/quantops_test_s6h82.duckdb"
if (Test-Path $env:QUANTOPS_DB_PATH) { Remove-Item $env:QUANTOPS_DB_PATH -Force }
Push-Location apps/quantops-api
python -m pytest app/tests/test_sprint6h8_2_scheduler_resume_block.py app/tests/test_sprint6h8_3_execution_resilience.py -q
Pop-Location

Write-Host "[4/4] Completed"
