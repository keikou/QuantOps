$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot

$job = $null

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
            $health = Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
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

    if (-not $healthOk) {
        $jobOutput = ""
        if ($job) {
            $jobOutput = Receive-Job -Job $job -ErrorAction SilentlyContinue | Out-String
        }
        throw "API health check timed out.`n$jobOutput"
    }

    $runOnce = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/run-once" -TimeoutSec 30
    if ($null -eq $runOnce.signals) {
        throw "run-once response did not include signals."
    }

    $alphaAnalytics = Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/analytics/alpha-performance" -TimeoutSec 15
    if ($null -eq $alphaAnalytics) {
        throw "alpha analytics endpoint returned null."
    }

    $regimeAnalytics = Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/analytics/regime-performance" -TimeoutSec 15
    if ($null -eq $regimeAnalytics) {
        throw "regime analytics endpoint returned null."
    }

    Write-Host "Health, run-once, alpha analytics, and regime analytics checks passed." -ForegroundColor Green
}
finally {
    Cleanup-ApiJob -Job $job
}
