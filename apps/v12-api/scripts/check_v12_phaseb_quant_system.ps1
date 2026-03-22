$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot

$job = $null

$expectedAlphas = @(
    'trend_alpha',
    'mean_reversion_alpha',
    'breakout_alpha',
    'funding_squeeze_alpha',
    'oi_divergence_alpha',
    'liquidation_hunt_alpha',
    'orderbook_imbalance_alpha',
    'volume_spike_alpha',
    'multi_horizon_momentum_alpha',
    'short_term_reversal_alpha',
    'funding_carry_alpha',
    'aggressive_trade_flow_alpha',
    'liquidation_cascade_alpha',
    'volatility_expansion_alpha',
    'vwap_mean_reversion_alpha',
    'volatility_band_reversion_alpha',
    'liquidity_sweep_reversion_alpha',
    'funding_mean_reversion_alpha',
    'oi_momentum_trend_alpha',
    'cross_asset_relative_momentum_alpha'
)

function Cleanup-ApiJob {
    param(
        [Parameter(Mandatory = $false)]
        $Job
    )

    if ($null -eq $Job) {
        return
    }

    try {
        $currentJob = Get-Job -Id $Job.Id -ErrorAction SilentlyContinue
        if ($null -eq $currentJob) {
            return
        }

        if ($currentJob.State -eq "Running") {
            Stop-Job -Job $currentJob -ErrorAction SilentlyContinue | Out-Null
        }

        Receive-Job -Job $currentJob -ErrorAction SilentlyContinue | Out-Null
        Remove-Job -Job $currentJob -ErrorAction SilentlyContinue | Out-Null
    }
    catch {
        Write-Warning ("Cleanup warning: " + $_.Exception.Message)
    }
}

function Assert-Condition {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

function Get-Json {
    param(
        [string]$Method,
        [string]$Uri,
        [int]$TimeoutSec = 30
    )

    return Invoke-RestMethod -Method $Method -Uri $Uri -TimeoutSec $TimeoutSec
}

try {
    Write-Host "Running pytest..." -ForegroundColor Cyan
    python -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "pytest failed."
    }

    Write-Host "Starting local API health check..." -ForegroundColor Cyan

    $job = Start-Job -ScriptBlock {
        param($RootPath)
        Set-Location $RootPath
        $env:PYTHONPATH = $RootPath
        python -m uvicorn ai_hedge_bot.api.app:app --host 127.0.0.1 --port 8000
    } -ArgumentList $projectRoot

    $healthOk = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        try {
            $health = Get-Json -Method GET -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
            if ($health.status -eq "ok") {
                $healthOk = $true
                break
            }
        }
        catch {
        }

        if ($job.State -match "Failed|Stopped|Completed") {
            $jobOutput = Receive-Job -Job $job -ErrorAction SilentlyContinue | Out-String
            throw "API job exited unexpectedly.`n$jobOutput"
        }
    }

    Assert-Condition $healthOk "API health check timed out."

    $featureSchema = Get-Json -Method GET -Uri "http://127.0.0.1:8000/features/schema" -TimeoutSec 15
    Assert-Condition ($featureSchema.count -eq 40) "Feature schema count was expected to be 40."

    $alphaRegistry = Get-Json -Method GET -Uri "http://127.0.0.1:8000/alpha/registry" -TimeoutSec 15
    Assert-Condition ($alphaRegistry.count -eq 20) "Alpha registry count was expected to be 20."

    $missingRegistryAlphas = @($expectedAlphas | Where-Object { $_ -notin $alphaRegistry.alphas })
    Assert-Condition ($missingRegistryAlphas.Count -eq 0) ("Alpha registry missing expected alphas: " + ($missingRegistryAlphas -join ", "))

    $weightsBefore = Get-Json -Method GET -Uri "http://127.0.0.1:8000/weights" -TimeoutSec 15
    $weightKeys = @($weightsBefore.PSObject.Properties.Name)
    $missingWeightKeys = @($expectedAlphas | Where-Object { $_ -notin $weightKeys })
    Assert-Condition ($missingWeightKeys.Count -eq 0) ("Weights endpoint missing expected alpha keys: " + ($missingWeightKeys -join ", "))

    $runOnce = Get-Json -Method POST -Uri "http://127.0.0.1:8000/run-once" -TimeoutSec 60
    Assert-Condition ($null -ne $runOnce.signals) "run-once response did not include signals."
    Assert-Condition ($runOnce.signals.Count -gt 0) "run-once returned zero signals."

    $seenAlphaNames = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($signal in $runOnce.signals) {
        Assert-Condition ($null -ne $signal.alpha_results) ("Signal " + $signal.signal_id + " did not include alpha_results.")
        Assert-Condition ($signal.alpha_results.Count -eq 20) ("Signal " + $signal.signal_id + " did not include all 20 alpha results.")

        foreach ($alphaResult in $signal.alpha_results) {
            $alphaName = $alphaResult.metadata.alpha_name
            if ($null -ne $alphaName) {
                [void]$seenAlphaNames.Add([string]$alphaName)
            }
        }
    }

    $missingSeenAlphas = @($expectedAlphas | Where-Object { -not $seenAlphaNames.Contains($_) })
    Assert-Condition ($missingSeenAlphas.Count -eq 0) ("run-once alpha_results did not cover all expected alphas: " + ($missingSeenAlphas -join ", "))

    $positions = Get-Json -Method GET -Uri "http://127.0.0.1:8000/positions" -TimeoutSec 15
    Assert-Condition ($null -ne $positions) "Positions endpoint returned null."

    $alphaAnalytics = Get-Json -Method GET -Uri "http://127.0.0.1:8000/analytics/alpha-performance" -TimeoutSec 30
    Assert-Condition ($null -ne $alphaAnalytics) "alpha analytics endpoint returned null."
    Assert-Condition ($alphaAnalytics.Count -ge 20) "alpha analytics did not return at least 20 rows."
    $alphaAnalyticsNames = @($alphaAnalytics | ForEach-Object { $_.alpha_name })
    $missingAnalyticsAlphas = @($expectedAlphas | Where-Object { $_ -notin $alphaAnalyticsNames })
    Assert-Condition ($missingAnalyticsAlphas.Count -eq 0) ("alpha analytics missing expected alphas: " + ($missingAnalyticsAlphas -join ", "))

    $regimeAnalytics = Get-Json -Method GET -Uri "http://127.0.0.1:8000/analytics/regime-performance" -TimeoutSec 30
    Assert-Condition ($null -ne $regimeAnalytics) "regime analytics endpoint returned null."
    Assert-Condition ($regimeAnalytics.Count -gt 0) "regime analytics returned zero rows."

    $portfolioDiagnostics = Get-Json -Method GET -Uri "http://127.0.0.1:8000/analytics/portfolio-diagnostics" -TimeoutSec 30
    Assert-Condition ($null -ne $portfolioDiagnostics) "portfolio diagnostics endpoint returned null."
    $diagRows = @($portfolioDiagnostics)
    Assert-Condition ($diagRows.Count -gt 0) "portfolio diagnostics returned zero rows."
    $latestDiag = $diagRows[0]
    Assert-Condition ($null -ne $latestDiag.input_signal_count) "portfolio diagnostics missing input_signal_count."
    Assert-Condition ($null -ne $latestDiag.selected_count) "portfolio diagnostics missing selected_count."
    Assert-Condition ($null -ne $latestDiag.family_concentration) "portfolio diagnostics missing family_concentration."

    $weightHistoryBeforeNightly = Get-Json -Method GET -Uri "http://127.0.0.1:8000/analytics/weight-history" -TimeoutSec 30
    Assert-Condition ($null -ne $weightHistoryBeforeNightly) "weight history endpoint returned null."
    $beforeCount = @($weightHistoryBeforeNightly).Count

    Write-Host "Running nightly scheduler check..." -ForegroundColor Cyan
    $nightlyOutput = python -m ai_hedge_bot.scheduler.nightly_weight_update
    if ($LASTEXITCODE -ne 0) {
        throw "nightly scheduler command failed."
    }

    $rebuild = Get-Json -Method POST -Uri "http://127.0.0.1:8000/analytics/rebuild" -TimeoutSec 30
    Assert-Condition ($null -ne $rebuild) "analytics rebuild endpoint returned null."

    $weightHistoryAfterNightly = Get-Json -Method GET -Uri "http://127.0.0.1:8000/analytics/weight-history" -TimeoutSec 30
    Assert-Condition ($null -ne $weightHistoryAfterNightly) "weight history endpoint returned null after nightly scheduler."
    $afterCount = @($weightHistoryAfterNightly).Count
    Assert-Condition ($afterCount -ge $beforeCount) "weight history count did not remain stable or grow after nightly scheduler."

    Write-Host "Health, features schema, alpha registry, all 20 alpha evaluations, positions, alpha analytics, regime analytics, portfolio diagnostics, nightly scheduler, analytics rebuild, and weight history checks passed." -ForegroundColor Green
}
finally {
    Cleanup-ApiJob -Job $job
}
