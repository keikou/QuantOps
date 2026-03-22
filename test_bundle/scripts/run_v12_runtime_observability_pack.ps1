param(
  [ValidateSet("blocked", "no_op", "degraded", "success", "all")]
  [string]$Pack = "all"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")
Set-Location $RepoRoot

$packArgs = @{
  blocked = @("tests/test_sprint6h9_2_8_runtime_event_truth.py", "-k", "blocked_cycle_reason_code or planned_not_submitted_cycle")
  no_op = @("tests/test_sprint6h9_2_8_runtime_event_truth.py", "-k", "no_decisions_exist or no_decision_cycle")
  degraded = @("tests/test_sprint6h9_2_8_runtime_event_truth.py", "-k", "stale_price_degradation_reason or submitted_no_fill_reason")
  success = @("tests/test_sprint6h9_2_8_runtime_event_truth.py", "-k", "successful_cycle_truth")
}

if ($Pack -eq "all") {
  $selectedPacks = @("blocked", "no_op", "degraded", "success")
} else {
  $selectedPacks = @($Pack)
}

Push-Location (Join-Path $RepoRoot "apps/v12-api")
try {
  foreach ($selectedPack in $selectedPacks) {
    Write-Host ("=== V12 runtime observability pack: {0} ===" -f $selectedPack)
    & ".venv\Scripts\python.exe" -m pytest @($packArgs[$selectedPack]) -q
  }
}
finally {
  Pop-Location
}
