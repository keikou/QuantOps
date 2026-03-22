$ErrorActionPreference = 'Stop'

$checks = @(
  'http://localhost:8000/health',
  'http://localhost:8000/runtime/run-once',
  'http://localhost:8000/runtime/runs',
  'http://localhost:8000/scheduler/jobs',
  'http://localhost:8000/scheduler/runs',
  'http://localhost:8000/strategy/signals/latest',
  'http://localhost:8000/portfolio/overview',
  'http://localhost:8000/execution/quality/latest'
)

foreach ($url in $checks) {
  if ($url -like '*/runtime/run-once') {
    $resp = Invoke-WebRequest -Method POST -Uri $url
  } else {
    $resp = Invoke-WebRequest -Method GET -Uri $url
  }
  if ($resp.StatusCode -ne 200) { throw "FAIL $url" }
  Write-Host "[PASS] $url $($resp.StatusCode)"
}
