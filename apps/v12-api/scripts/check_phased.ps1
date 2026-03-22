param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$RunCycleCount = 3,
    [switch]$SkipPytest,
    [switch]$StartLocalApi
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot
$apiJob = $null

function Cleanup-ApiJob { param($Job) if ($null -eq $Job) { return } try { if ($Job.State -eq 'Running') { Stop-Job -Job $Job -ErrorAction SilentlyContinue | Out-Null }; Receive-Job -Job $Job -ErrorAction SilentlyContinue | Out-Null; Remove-Job -Job $Job -ErrorAction SilentlyContinue | Out-Null } catch {} }
function Get-Json([string]$Method,[string]$Uri){ return Invoke-RestMethod -Method $Method -Uri $Uri -TimeoutSec 60 }
function Assert-Condition([bool]$Condition,[string]$Message){ if(-not $Condition){ throw $Message } }
function As-Array($obj) {
    if ($null -eq $obj) { return @() }
    if ($obj -is [System.Array]) { return $obj }
    if ($obj -is [System.Collections.IEnumerable] -and -not ($obj -is [string])) {
        return @($obj)
    }
    return @($obj)
}

try {
    if (-not $SkipPytest) { python -m pytest -q; if ($LASTEXITCODE -ne 0) { throw 'pytest failed.' } }
    if ($StartLocalApi) {
        $apiJob = Start-Job -ScriptBlock { param($RootPath) Set-Location $RootPath; $env:PYTHONPATH = $RootPath; python -m uvicorn ai_hedge_bot.api.app:app --host 127.0.0.1 --port 8000 } -ArgumentList $projectRoot
        $ok = $false
        for($i=0; $i -lt 45; $i++){ Start-Sleep -Seconds 1; try { $h = Get-Json GET "$BaseUrl/health"; if($h.status -eq 'ok'){ $ok = $true; break } } catch {} }
        Assert-Condition $ok 'API health check timed out.'
    }

    $health = Get-Json GET "$BaseUrl/health"
    Assert-Condition ($health.phase -eq 'D') 'health phase must be D'

    $run = Get-Json POST "$BaseUrl/run-once"
    Assert-Condition ($null -ne $run.phase_d) 'run-once missing phase_d'
    Assert-Condition ($run.phase_d.shadow_order_count -ge 1) 'shadow_order_count must be >= 1'

    for($i=0; $i -lt $RunCycleCount; $i++){ $null = Get-Json POST "$BaseUrl/runner/run-cycle" }

    $summary = Get-Json GET "$BaseUrl/analytics/shadow-summary"
    Assert-Condition ($summary.orders_count -ge 1) 'shadow summary orders_count must be >= 1'
    Assert-Condition ($summary.fills_count -ge 1) 'shadow summary fills_count must be >= 1'

    $orders = As-Array (Get-Json GET "$BaseUrl/execution/shadow-orders")
    $fills = As-Array (Get-Json GET "$BaseUrl/execution/shadow-fills")
    $life = As-Array (Get-Json GET "$BaseUrl/analytics/order-lifecycle")
    $latency = As-Array (Get-Json GET "$BaseUrl/execution/latency")
    $quality = As-Array (Get-Json GET "$BaseUrl/analytics/execution-quality")
    $slippage = As-Array (Get-Json GET "$BaseUrl/analytics/slippage-report")

    Assert-Condition ($orders.Count -ge 1) 'shadow-orders returned zero rows'
    Assert-Condition ($fills.Count -ge 1) 'shadow-fills returned zero rows'
    Assert-Condition ($life.Count -ge 1) 'order-lifecycle returned zero rows'
    $hasTerminalTransition = $false
    foreach ($row in $life) {
        if ($row.to_state -eq 'filled' -or $row.to_state -eq 'partial') {
            $hasTerminalTransition = $true
            break
        }
    }
    Assert-Condition $hasTerminalTransition 'order-lifecycle missing filled/partial transition'
    Assert-Condition ($latency.Count -ge 1) 'execution/latency returned zero rows'
    Assert-Condition ($quality.Count -ge 1) 'execution-quality returned zero rows'
    Assert-Condition ($slippage.Count -ge 1) 'slippage-report returned zero rows'

    Write-Host 'PhaseD verification passed.' -ForegroundColor Green
}
finally { Cleanup-ApiJob $apiJob }
