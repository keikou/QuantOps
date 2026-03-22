$ErrorActionPreference = "Continue"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = ".\logs\Sprint6_E2E_$timestamp"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Save-Command {
    param($name, $cmd)

    Write-Host "Running: $name"
    $outfile = "$logDir\$name.txt"

    try {
        $result = Invoke-Expression $cmd | Out-String
        $result | Out-File $outfile
    }
    catch {
        $_ | Out-File $outfile
    }
}

function Save-Rest {
    param($name, $url)

    Write-Host "Calling API: $url"
    $outfile = "$logDir\$name.json"

    try {
        $result = Invoke-RestMethod $url -TimeoutSec 20
        $result | ConvertTo-Json -Depth 20 | Out-File $outfile
    }
    catch {
        $_ | Out-File $outfile
    }
}

Write-Host "===== STEP1 Docker 状態 ====="

Save-Command "docker_ps" "docker ps"
Save-Command "docker_ps_a" "docker ps -a"
Save-Command "docker_compose_ps" "docker compose ps"

Write-Host "===== STEP2 Docker Logs ====="

Save-Command "worker_logs_before" "docker compose logs quantops-worker --tail=200"
Save-Command "api_logs_before" "docker compose logs quantops-api --tail=200"
Save-Command "v12_logs_before" "docker compose logs v12-api --tail=200"

Write-Host "===== STEP3 API Snapshot BEFORE ====="

Save-Rest "v12_health" "http://localhost:8000/health"
Save-Rest "quantops_health" "http://localhost:8010/api/v1/health"
Save-Rest "portfolio_before" "http://localhost:8010/api/v1/portfolio/positions"
Save-Rest "dashboard_before" "http://localhost:8010/api/v1/dashboard/overview"
Save-Rest "analytics_before" "http://localhost:8010/api/v1/analytics/alpha"
Save-Rest "risk_before" "http://localhost:8010/api/v1/risk/snapshot"

Write-Host "===== WAITING NEXT PAPER TRADING CYCLE ====="

Start-Sleep -Seconds 70

Write-Host "===== STEP4 API Snapshot AFTER ====="

Save-Rest "portfolio_after" "http://localhost:8010/api/v1/portfolio/positions"
Save-Rest "dashboard_after" "http://localhost:8010/api/v1/dashboard/overview"
Save-Rest "analytics_after" "http://localhost:8010/api/v1/analytics/alpha"
Save-Rest "risk_after" "http://localhost:8010/api/v1/risk/snapshot"

Write-Host "===== STEP5 Docker Logs AFTER ====="

Save-Command "worker_logs_after" "docker compose logs quantops-worker --tail=200"
Save-Command "api_logs_after" "docker compose logs quantops-api --tail=200"
Save-Command "v12_logs_after" "docker compose logs v12-api --tail=200"

Write-Host ""
Write-Host "Logs saved to:"
Write-Host $logDir