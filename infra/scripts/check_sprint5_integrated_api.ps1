$ErrorActionPreference = "Stop"
$targets = @(
  "http://localhost:8000/system/health",
  "http://localhost:8000/runtime/runs",
  "http://localhost:8000/risk/latest",
  "http://localhost:8000/analytics/performance",
  "http://localhost:8000/governance/regime",
  "http://localhost:8000/runtime/modes/current",
  "http://localhost:8000/acceptance/status",
  "http://localhost:8000/incidents/latest",
  "http://localhost:8000/analytics/shadow-summary",
  "http://localhost:8010/api/v1/health",
  "http://localhost:8010/api/v1/modes/current",
  "http://localhost:8010/api/v1/acceptance/status",
  "http://localhost:8010/api/v1/incidents/latest",
  "http://localhost:8010/api/v1/risk/latest",
  "http://localhost:8010/api/v1/analytics/performance",
  "http://localhost:8010/api/v1/governance/regime"
)
foreach ($url in $targets) {
  try {
    $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
    if ($resp.StatusCode -eq 200) {
      Write-Host "[PASS] $url 200"
    } else {
      Write-Host "[FAIL] $url $($resp.StatusCode)"
      exit 1
    }
  } catch {
    Write-Host "[FAIL] $url $($_.Exception.Message)"
    exit 1
  }
}
Write-Host "Sprint5 integrated API check completed."
