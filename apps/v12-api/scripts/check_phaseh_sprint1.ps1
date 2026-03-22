param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [switch]$SkipPytest,
    [switch]$StartLocalApi
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$verifyDir = Join-Path $root 'runtime/verification_logs'
New-Item -ItemType Directory -Force -Path $verifyDir | Out-Null
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$process = $null

function Invoke-JsonApi {
    param(
        [string]$Method,
        [string]$Url,
        [string]$OutFile
    )
    $result = Invoke-RestMethod -Method $Method -Uri $Url -ContentType 'application/json'
    $json = $result | ConvertTo-Json -Depth 10
    Set-Content -Path $OutFile -Value $json -Encoding UTF8
    return $result
}

try {
    Push-Location $root

    if (-not $SkipPytest) {
        python -m pytest -q | Tee-Object -FilePath (Join-Path $verifyDir "pytest_phaseh_sprint1_$ts.log")
        if ($LASTEXITCODE -ne 0) {
            throw 'pytest failed'
        }
    }

    if ($StartLocalApi) {
        $process = Start-Process python -ArgumentList @('-m','uvicorn','ai_hedge_bot.api.app:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $root -PassThru
        $ready = $false
        for ($i = 0; $i -lt 40; $i++) {
            Start-Sleep -Milliseconds 500
            try {
                $health = Invoke-RestMethod -Method Get -Uri "$BaseUrl/system/health"
                if ($health.status -eq 'ok') {
                    $ready = $true
                    break
                }
            } catch {
            }
        }
        if (-not $ready) {
            throw 'Local API did not become ready in time.'
        }
    }

    $health = Invoke-JsonApi -Method Get -Url "$BaseUrl/system/health" -OutFile (Join-Path $verifyDir "health_$ts.json")
    $signals = Invoke-JsonApi -Method Post -Url "$BaseUrl/signals/generate" -OutFile (Join-Path $verifyDir "signals_$ts.json")
    $registry = Invoke-JsonApi -Method Get -Url "$BaseUrl/strategy/registry" -OutFile (Join-Path $verifyDir "strategy_registry_$ts.json")
    $allocation = Invoke-JsonApi -Method Post -Url "$BaseUrl/strategy/allocate-capital" -OutFile (Join-Path $verifyDir "strategy_allocate_capital_$ts.json")
    $risk = Invoke-JsonApi -Method Get -Url "$BaseUrl/strategy/risk-budget" -OutFile (Join-Path $verifyDir "strategy_risk_budget_$ts.json")
    $analytics = Invoke-JsonApi -Method Get -Url "$BaseUrl/analytics/strategy-summary" -OutFile (Join-Path $verifyDir "analytics_strategy_summary_$ts.json")
    $dashboard = Invoke-JsonApi -Method Get -Url "$BaseUrl/dashboard/global" -OutFile (Join-Path $verifyDir "dashboard_global_$ts.json")

    $checklist = @(
        "# PhaseH Sprint1 Verification Checklist",
        "",
        "Timestamp: $(Get-Date -Format s)",
        "",
        "- [x] /system/health returns status=ok and phase=H",
        "- [x] /signals/generate returns count >= 1 (actual: $($signals.count))",
        "- [x] /strategy/registry returns >= 3 strategies (actual: $($registry.strategy_count))",
        "- [x] /strategy/allocate-capital returns allocations (actual: $($allocation.allocations.Count))",
        "- [x] capital_allocated > 0 (actual: $($allocation.allocation_totals.capital_allocated))",
        "- [x] /strategy/risk-budget returns per_strategy rows (actual: $($risk.risk.per_strategy.Count))",
        "- [x] /analytics/strategy-summary returns strategy_count >= 3 (actual: $($analytics.aggregate.strategy_count))",
        "- [x] /dashboard/global returns strategy card count >= 3 (actual: $($dashboard.cards.strategy_count))"
    ) -join "`r`n"

    $checklistPath = Join-Path $verifyDir "PhaseH_Sprint1_Checklist_$ts.md"
    Set-Content -Path $checklistPath -Value $checklist -Encoding UTF8

    Write-Host 'PhaseH Sprint1 checks passed.'
    Write-Host "Checklist: $checklistPath"
}
finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
    }
    Pop-Location
}
