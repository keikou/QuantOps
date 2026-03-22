$ErrorActionPreference = "Stop"
$checks = @(
  "http://localhost:8000/health",
  "http://localhost:8010/api/v1/health",
  "http://localhost:8010/docs",
  "http://localhost:8000/strategy/registry",
  "http://localhost:8000/strategy/risk-budget",
  "http://localhost:8000/execution/quality/latest",
  "http://localhost:8000/portfolio/diagnostics/latest",
  "http://localhost:8000/dashboard/global",
  "http://localhost:8010/api/v1/dashboard/overview",
  "http://localhost:8010/api/v1/portfolio/overview",
  "http://localhost:8010/api/v1/analytics/summary",
  "http://localhost:8010/api/v1/risk/snapshot",
  "http://localhost:8010/api/v1/monitoring/system",
  "http://localhost:8010/api/v1/alerts",
  "http://localhost:8010/api/v1/scheduler/jobs"
)

foreach($u in $checks){
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 20
    Write-Host "[PASS] $u $($r.StatusCode)"
  } catch {
    Write-Host "[FAIL] $u $($_.Exception.Message)"
  }
}
