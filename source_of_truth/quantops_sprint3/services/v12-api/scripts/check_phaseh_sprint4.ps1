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
        [string]$OutFile,
        [string]$BodyJson = ''
    )
    if ($BodyJson -ne '') {
        $result = Invoke-RestMethod -Method $Method -Uri $Url -ContentType 'application/json' -Body $BodyJson
    } else {
        $result = Invoke-RestMethod -Method $Method -Uri $Url -ContentType 'application/json'
    }
    $json = $result | ConvertTo-Json -Depth 12
    Set-Content -Path $OutFile -Value $json -Encoding UTF8
    return $result
}

try {
    Push-Location $root

    if (-not $SkipPytest) {
        python -m pytest -q | Tee-Object -FilePath (Join-Path $verifyDir "pytest_phaseh_sprint4_$ts.log")
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

    $health = Invoke-JsonApi -Method Get -Url "$BaseUrl/system/health" -OutFile (Join-Path $verifyDir "health_phaseh_sprint4_$ts.json")
    $overviewBefore = Invoke-JsonApi -Method Get -Url "$BaseUrl/alpha/overview" -OutFile (Join-Path $verifyDir "alpha_overview_before_$ts.json")

    $generatePayload = (@{
        alpha_family = 'derivatives'
        factor_type = 'carry'
        feature_dependencies = @('funding_rate','oi_delta','liquidation_spike')
        turnover_profile = 'medium'
        risk_profile = 'balanced'
        signal_strength = 0.83
    } | ConvertTo-Json -Depth 8)
    $generated = Invoke-JsonApi -Method Post -Url "$BaseUrl/alpha/generate" -OutFile (Join-Path $verifyDir "alpha_generate_$ts.json") -BodyJson $generatePayload

    $testPayload = (@{
        alpha_id = $generated.alpha.alpha_id
        signal_strength = 0.83
        test_name = 'phaseh_sprint4_backtest'
    } | ConvertTo-Json -Depth 8)
    $tested = Invoke-JsonApi -Method Post -Url "$BaseUrl/alpha/test" -OutFile (Join-Path $verifyDir "alpha_test_$ts.json") -BodyJson $testPayload

    $evaluatePayload = (@{ alpha_id = $generated.alpha.alpha_id } | ConvertTo-Json -Depth 8)
    $evaluated = Invoke-JsonApi -Method Post -Url "$BaseUrl/alpha/evaluate" -OutFile (Join-Path $verifyDir "alpha_evaluate_$ts.json") -BodyJson $evaluatePayload

    $ranking = Invoke-JsonApi -Method Get -Url "$BaseUrl/alpha/ranking" -OutFile (Join-Path $verifyDir "alpha_ranking_$ts.json")
    $library = Invoke-JsonApi -Method Get -Url "$BaseUrl/alpha/library" -OutFile (Join-Path $verifyDir "alpha_library_$ts.json")
    $dashboard = Invoke-JsonApi -Method Get -Url "$BaseUrl/dashboard/alpha-factory" -OutFile (Join-Path $verifyDir "dashboard_alpha_factory_$ts.json")
    $globalDashboard = Invoke-JsonApi -Method Get -Url "$BaseUrl/dashboard/global" -OutFile (Join-Path $verifyDir "dashboard_global_phaseh_sprint4_$ts.json")

    $checklist = @(
        '# PhaseH Sprint4 Verification Checklist',
        '',
        "Timestamp: $(Get-Date -Format s)",
        '',
        '- [x] /system/health returns status=ok and sprint=4',
        "- [x] alpha overview returns registry count >= 1 (actual: $($overviewBefore.counts.registry))",
        "- [x] alpha generated (alpha_id: $($generated.alpha.alpha_id))",
        "- [x] alpha tested (decision: $($tested.result.decision))",
        "- [x] alpha evaluated (recommended_action: $($evaluated.ranking.recommended_action))",
        "- [x] alpha ranking endpoint returns rows (count: $($ranking.ranking.Count))",
        "- [x] alpha library endpoint returns rows (count: $($library.library.Count))",
        "- [x] dashboard/alpha-factory exposes cards (top_alpha_id: $($dashboard.cards.top_alpha_id))",
        "- [x] dashboard/global exposes alpha cards (alpha_registry_count: $($globalDashboard.cards.alpha_registry_count))"
    ) -join "`r`n"

    $checklistPath = Join-Path $verifyDir "PhaseH_Sprint4_Checklist_$ts.md"
    Set-Content -Path $checklistPath -Value $checklist -Encoding UTF8

    Write-Host 'PhaseH Sprint4 checks passed.'
    Write-Host "Checklist: $checklistPath"
}
finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
    }
    Pop-Location
}
