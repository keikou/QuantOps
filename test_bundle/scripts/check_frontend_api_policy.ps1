param()

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")
Set-Location $RepoRoot

function Assert-Pattern {
  param(
    [string]$Content,
    [string]$Pattern,
    [string]$Message
  )

  if ($Content -notmatch $Pattern) {
    throw $Message
  }
}

$config = Get-Content "apps/quantops-frontend/src/lib/api/config.ts" -Raw
$fetcher = Get-Content "apps/quantops-frontend/src/lib/api/fetcher.ts" -Raw
$proxy = Get-Content -LiteralPath "apps/quantops-frontend/src/app/api/proxy/[...path]/route.ts" -Raw

Assert-Pattern $config "replace\(/\\/\+\$/, ''\)" 'config.ts must trim trailing slashes from QUANTOPS_API_BASE_URL.'
Assert-Pattern $config "127\.0\.0\.1:8010" 'config.ts must default QUANTOPS_API_BASE_URL to 127.0.0.1:8010.'

Assert-Pattern $proxy "replace\(/\\/\+\$/, ''\)" 'proxy route must trim trailing slashes from its upstream base URL.'
Assert-Pattern $proxy "127\.0\.0\.1:8010" 'proxy route must default its upstream base URL to 127.0.0.1:8010.'

Assert-Pattern $fetcher "path === '/api/v1/dashboard/overview'.*35000" 'fetcher.ts must keep the extended timeout for dashboard overview.'
Assert-Pattern $fetcher "path === '/api/v1/analytics/equity-history'.*30000" 'fetcher.ts must keep the extended timeout for analytics equity history.'
Assert-Pattern $fetcher "path === '/api/v1/monitoring/system'.*25000" 'fetcher.ts must keep the extended timeout for monitoring/system.'
Assert-Pattern $fetcher "path === '/api/v1/scheduler/jobs'.*15000" 'fetcher.ts must keep the extended timeout for scheduler/jobs.'
Assert-Pattern $fetcher "path === '/api/v1/portfolio/positions'.*12000" 'fetcher.ts must keep the extended timeout for portfolio positions.'
Assert-Pattern $fetcher "path === '/api/v1/portfolio/overview'.*12000" 'fetcher.ts must keep the extended timeout for portfolio overview.'

Write-Host "Frontend API policy checks passed."
