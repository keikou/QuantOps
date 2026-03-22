$ErrorActionPreference = "Stop"

$targets = @(
  "http://localhost:8010/api/v1/modes/current",
  "http://localhost:8010/api/v1/modes/config",
  "http://localhost:8010/api/v1/incidents/latest",
  "http://localhost:8010/api/v1/acceptance/status"
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
