$ErrorActionPreference = "Stop"

$checks = @(
  "http://localhost:8000/runtime/modes",
  "http://localhost:8000/runtime/modes/current",
  "http://localhost:8000/acceptance/status",
  "http://localhost:8000/incidents/latest",
  "http://localhost:8000/analytics/shadow-summary"
)

foreach ($url in $checks) {
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 5
    if ($resp.StatusCode -eq 200) {
      Write-Host "[PASS] $url $($resp.StatusCode)"
    } else {
      Write-Host "[FAIL] $url $($resp.StatusCode)"
    }
  } catch {
    Write-Host "[FAIL] $url $($_.Exception.Message)"
  }
}
