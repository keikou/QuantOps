param(
  [ValidateSet("truth", "stale", "debug", "all")]
  [string]$Pack = "all"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")
Set-Location $RepoRoot

$packTests = @{
  truth = @(
    "app/tests/test_sprint6h9_2_7_2_command_center_live_execution_bridge.py",
    "app/tests/test_sprint6h9_2_7_equity_breakdown_truth.py"
  )
  stale = @(
    "app/tests/test_sprint6h9_2_7_7_risk_snapshot_fast_path.py",
    "app/tests/test_sprint6h9_2_7_7_monitoring_fast_path.py"
  )
  debug = @(
    "app/tests/test_sprint6h9_2_7_9_debug_surfaces.py",
    "app/tests/test_sprint6h9_2_7_12_debug_contracts.py",
    "app/tests/test_sprint6h9_2_7_9b_execution_overview_debug.py",
    "app/tests/test_sprint6h9_2_7_9c_portfolio_debug.py"
  )
}

if ($Pack -eq "all") {
  $selectedPacks = @("truth", "stale", "debug")
} else {
  $selectedPacks = @($Pack)
}

$runtimeDir = Join-Path $RepoRoot "runtime"
if (-not (Test-Path $runtimeDir)) {
  New-Item -ItemType Directory -Path $runtimeDir | Out-Null
}

$env:PYTHONPATH = Join-Path $RepoRoot "apps/quantops-api"
$env:V12_MOCK_MODE = "true"

Push-Location (Join-Path $RepoRoot "apps/quantops-api")
try {
  foreach ($selectedPack in $selectedPacks) {
    $dbPath = Join-Path $runtimeDir ("quantops_ci_{0}.duckdb" -f $selectedPack)
    if (Test-Path $dbPath) {
      Remove-Item $dbPath -Force
    }
    $env:QUANTOPS_DB_PATH = $dbPath

    Write-Host ("=== QuantOps API regression pack: {0} ===" -f $selectedPack)
    foreach ($testPath in $packTests[$selectedPack]) {
      python -m pytest $testPath -q
    }
  }
}
finally {
  Pop-Location
}
