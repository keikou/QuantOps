param(
    [string]$BaseUrl = "http://127.0.0.1:8010"
)
$ErrorActionPreference = "Stop"
docker compose up --build -d | Out-Null
Start-Sleep -Seconds 2
try {
    $health = Invoke-RestMethod "$BaseUrl/api/v1/health"
    if ($health.status -ne "ok") { throw "health check failed" }
    Invoke-RestMethod -Method Post "$BaseUrl/api/v1/monitoring/refresh" | Out-Null
    Invoke-RestMethod -Method Post "$BaseUrl/api/v1/analytics/refresh" | Out-Null
    $gov = Invoke-RestMethod -Method Post "$BaseUrl/api/v1/governance/refresh"
    $req = Invoke-RestMethod -Method Post "$BaseUrl/api/v1/approval/request" -ContentType "application/json" -Body '{"request_type":"promotion","target_id":"s1","requested_by":"operator","summary":{"reason":"qa"}}'
    Invoke-RestMethod -Method Post "$BaseUrl/api/v1/incidents/create" -ContentType "application/json" -Body '{"incident_type":"service_unhealthy","severity":"medium","title":"Test incident","description":"one-step validation"}' | Out-Null
    Invoke-RestMethod "$BaseUrl/api/v1/alerts" | Out-Null
    Invoke-RestMethod "$BaseUrl/api/v1/admin/audit-logs" | Out-Null
    if (-not $req.request_id) { throw "approval request missing" }
    Write-Host "Sprint2-integrated Sprint3 Docker one-step verification passed."
}
finally {
    docker compose down | Out-Null
}
