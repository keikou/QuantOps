param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$RunCycleCount = 3,
    [string]$OutputDir = "runtime/verification_logs"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

$resolvedOutDir = if ([System.IO.Path]::IsPathRooted($OutputDir)) { $OutputDir } else { Join-Path $projectRoot $OutputDir }
New-Item -ItemType Directory -Force -Path $resolvedOutDir | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$summaryFile = Join-Path $resolvedOutDir ("phase_d_cycle_summary_" + $timestamp + ".json")
$traceFile = Join-Path $resolvedOutDir ("phase_d_cycle_trace_" + $timestamp + ".log")

function Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $traceFile -Value $line
}

function Wait-Api {
    param([string]$Url)
    for ($i=0; $i -lt 60; $i++) {
        try {
            $h = Invoke-RestMethod -Method GET -Uri "$Url/health" -TimeoutSec 5
            if ($h.status -eq "ok" -and $h.phase -eq "D") { return $h }
        } catch {}
        Start-Sleep -Seconds 2
    }
    throw "API not ready"
}

function Invoke-Json {
    param(
        [string]$Method,
        [string]$Path,
        [string]$Tag
    )
    $uri = "$BaseUrl$Path"
    Log ("{0} {1}" -f $Method, $uri)
    $resp = Invoke-RestMethod -Method $Method -Uri $uri -TimeoutSec 60
    $jsonPath = Join-Path $resolvedOutDir ($Tag + "_" + $timestamp + ".json")
    $resp | ConvertTo-Json -Depth 10 | Set-Content -Path $jsonPath -Encoding UTF8
    return $resp
}

function As-Array($obj) {
    if ($null -eq $obj) { return @() }
    if ($obj -is [System.Array]) { return $obj }
    if ($obj -is [System.Collections.IEnumerable] -and -not ($obj -is [string])) { return @($obj) }
    return @($obj)
}

function Assert-Condition([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

$health = Wait-Api -Url $BaseUrl
Log ("API ready. phase={0} mode={1}" -f $health.phase, $health.mode)

$runOnce = Invoke-Json -Method POST -Path "/run-once" -Tag "run_once"
Assert-Condition ($null -ne $runOnce.phase_d) 'run-once missing phase_d payload'
Assert-Condition ($runOnce.phase_d.shadow_order_count -ge 1) 'run-once did not generate shadow orders'
Log ("run-once complete. shadow_order_count={0}" -f $runOnce.phase_d.shadow_order_count)

$cycleResponses = @()
for ($i=1; $i -le $RunCycleCount; $i++) {
    $cycle = Invoke-Json -Method POST -Path "/runner/run-cycle" -Tag ("runner_cycle_" + $i)
    $cycleResponses += $cycle
    $shadowOrderCount = if ($cycle.phase_d -and $cycle.phase_d.shadow_order_count) { $cycle.phase_d.shadow_order_count } else { 0 }
    Log ("runner-cycle #{0} complete. shadow_order_count={1}" -f $i, $shadowOrderCount)
}

$summary = Invoke-Json -Method GET -Path "/analytics/shadow-summary" -Tag "shadow_summary"
$orders = As-Array (Invoke-Json -Method GET -Path "/execution/shadow-orders" -Tag "shadow_orders")
$fills = As-Array (Invoke-Json -Method GET -Path "/execution/shadow-fills" -Tag "shadow_fills")
$lifecycle = As-Array (Invoke-Json -Method GET -Path "/analytics/order-lifecycle" -Tag "order_lifecycle")
$latency = As-Array (Invoke-Json -Method GET -Path "/execution/latency" -Tag "latency")
$quality = As-Array (Invoke-Json -Method GET -Path "/analytics/execution-quality" -Tag "execution_quality")
$slippage = As-Array (Invoke-Json -Method GET -Path "/analytics/slippage-report" -Tag "slippage_report")

Assert-Condition ($summary.orders_count -ge 1) 'shadow summary orders_count must be >= 1'
Assert-Condition ($summary.fills_count -ge 1) 'shadow summary fills_count must be >= 1'
Assert-Condition ($orders.Count -ge 1) 'shadow-orders returned zero rows'
Assert-Condition ($fills.Count -ge 1) 'shadow-fills returned zero rows'
Assert-Condition ($lifecycle.Count -ge 1) 'order-lifecycle returned zero rows'
Assert-Condition ($latency.Count -ge 1) 'latency returned zero rows'
Assert-Condition ($quality.Count -ge 1) 'execution-quality returned zero rows'
Assert-Condition ($slippage.Count -ge 1) 'slippage-report returned zero rows'

$hasTerminalTransition = $false
foreach ($row in $lifecycle) {
    if ($row.to_state -eq 'filled' -or $row.to_state -eq 'partial') {
        $hasTerminalTransition = $true
        break
    }
}
Assert-Condition $hasTerminalTransition 'order-lifecycle missing filled/partial transition'

$final = [ordered]@{
    verified_at = (Get-Date).ToString("o")
    base_url = $BaseUrl
    run_cycle_count = $RunCycleCount
    health = $health
    run_once_shadow_order_count = $runOnce.phase_d.shadow_order_count
    shadow_summary = $summary
    orders_count = $orders.Count
    fills_count = $fills.Count
    lifecycle_count = $lifecycle.Count
    latency_count = $latency.Count
    quality_count = $quality.Count
    slippage_count = $slippage.Count
    output_dir = $resolvedOutDir
    trace_file = $traceFile
}

$final | ConvertTo-Json -Depth 10 | Set-Content -Path $summaryFile -Encoding UTF8
Log ("PhaseD cycle verification SUCCESS. summary_file={0}" -f $summaryFile)
