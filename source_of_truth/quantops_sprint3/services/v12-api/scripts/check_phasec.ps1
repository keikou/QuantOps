param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$OutputDir = ".\check_outputs",
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

function Write-Section($text) {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host $text -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
}

function Write-Ok($text) { Write-Host "[OK] $text" -ForegroundColor Green }
function Write-WarnMsg($text) { Write-Host "[WARN] $text" -ForegroundColor Yellow }
function Write-Ng($text) { Write-Host "[NG] $text" -ForegroundColor Red }

function Cleanup-ApiJob {
    param([Parameter(Mandatory = $false)] $Job)
    if ($null -eq $Job) { return }
    try {
        $currentJob = Get-Job -Id $Job.Id -ErrorAction SilentlyContinue
        if ($null -eq $currentJob) { return }
        if ($currentJob.State -eq "Running") { Stop-Job -Job $currentJob -ErrorAction SilentlyContinue | Out-Null }
        Receive-Job -Job $currentJob -ErrorAction SilentlyContinue | Out-Null
        Remove-Job -Job $currentJob -ErrorAction SilentlyContinue | Out-Null
    } catch {
        Write-WarnMsg ("Cleanup warning: " + $_.Exception.Message)
    }
}

function Save-JsonText($path, $content) {
    $dir = Split-Path -Parent $path
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $content | Out-File -FilePath $path -Encoding utf8
}

function Invoke-JsonGet($url, $savePath) {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $url -Method GET
    if ($response.StatusCode -ne 200) { throw "GET $url failed with status $($response.StatusCode)" }
    Save-JsonText -path $savePath -content $response.Content
    return ($response.Content | ConvertFrom-Json)
}

function Invoke-JsonPost($url, $savePath) {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $url -Method POST
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) { throw "POST $url failed with status $($response.StatusCode)" }
    Save-JsonText -path $savePath -content $response.Content
    return ($response.Content | ConvertFrom-Json)
}

function Assert-NotNull($value, $message) { if ($null -eq $value) { throw $message } }
function Assert-True($condition, $message) { if (-not $condition) { throw $message } }

function Get-PropertyIfExists($obj, $name) {
    if ($null -eq $obj) { return $null }
    $prop = $obj.PSObject.Properties[$name]
    if ($null -ne $prop) { return $prop.Value }
    return $null
}

function Get-ArrayCount($value) {
    if ($null -eq $value) { return 0 }
    if ($value -is [System.Array]) { return $value.Count }
    if ($value -is [System.Collections.IEnumerable] -and -not ($value -is [string])) {
        $count = 0
        foreach ($item in $value) { $count++ }
        return $count
    }
    return 1
}

function Get-LatestRecord($obj) {
    if ($null -eq $obj) { return $null }
    if ($obj -is [System.Array]) {
        if ($obj.Count -eq 0) { return $null }
        return $obj[0]
    }
    return $obj
}

function Filter-RecordsByPortfolioId($obj, $portfolioId) {
    if ($null -eq $obj) { return @() }
    if ($obj -is [System.Array]) {
        if ([string]::IsNullOrWhiteSpace($portfolioId)) { return $obj }
        return @($obj | Where-Object { (Get-PropertyIfExists -obj $_ -name "portfolio_id") -eq $portfolioId })
    }
    if ($obj -is [pscustomobject]) {
        if ([string]::IsNullOrWhiteSpace($portfolioId)) { return @($obj) }
        $rowPortfolioId = Get-PropertyIfExists -obj $obj -name "portfolio_id"
        if ($rowPortfolioId -eq $portfolioId) { return @($obj) }
    }
    return @()
}

function Sum-TargetWeights($weightsObj) {
    $sum = 0.0
    if ($null -eq $weightsObj) { return $sum }

    if ($weightsObj -is [System.Array]) {
        foreach ($item in $weightsObj) {
            $w = Get-PropertyIfExists -obj $item -name "target_weight"
            if ($null -ne $w) { $sum += [double]$w }
        }
        return $sum
    }

    $direct = Get-PropertyIfExists -obj $weightsObj -name "target_weight"
    if ($null -ne $direct) { return [double]$direct }

    return $sum
}

function Ensure-Pytest {
    if ($SkipPytest) {
        Write-WarnMsg "Skipping pytest because -SkipPytest was specified"
        return
    }
    Write-Section "0. Pytest"
    & "$scriptDir/run_tests.ps1"
    Write-Ok "run_tests.ps1 completed"
}

function Start-ApiIfNeeded {
    if (-not $StartLocalApi) {
        Write-WarnMsg "Assuming API is already running at $BaseUrl"
        return $null
    }

    Write-Section "API Bootstrap"
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
            $health = Invoke-RestMethod -Method GET -Uri "$BaseUrl/health" -TimeoutSec 5
            if ($health.status -eq "ok") { $healthOk = $true; break }
        } catch {}
    }
    if (-not $healthOk) { throw "API health check timed out while starting local API." }
    Write-Ok "Local API started and passed health check"
    return $job
}

function Test-Health {
    Write-Section "1. Health Check"
    $data = Invoke-JsonGet -url "$BaseUrl/health" -savePath "$OutputDir/health.json"
    $status = Get-PropertyIfExists -obj $data -name "status"
    Assert-NotNull $status "/health response does not contain status"
    Write-Ok "/health responded successfully"
}

function Test-RunOnce {
    Write-Section "2. Run Once"
    $data = Invoke-JsonPost -url "$BaseUrl/run-once" -savePath "$OutputDir/run_once.json"
    $signals = Get-PropertyIfExists -obj $data -name "signals"
    Assert-NotNull $signals "/run-once response does not contain signals"
    $signalCount = Get-ArrayCount $signals
    Assert-True ($signalCount -ge 1) "/run-once returned zero signals"
    $phaseC = Get-PropertyIfExists -obj $data -name "phase_c"
    Assert-NotNull $phaseC "/run-once response does not contain phase_c payload"
    Write-Ok "/run-once returned $signalCount signal(s) and phase_c payload"
}

function Test-PortfolioEndpoints {
    Write-Section "3. Portfolio Endpoints"
    $portfolioData = @{}
    $portfolioData.expectedReturns = Invoke-JsonGet -url "$BaseUrl/portfolio/expected-returns" -savePath "$OutputDir/expected_returns.json"
    Write-Ok "/portfolio/expected-returns OK"
    $portfolioData.weights = Invoke-JsonGet -url "$BaseUrl/portfolio/weights" -savePath "$OutputDir/weights.json"
    Write-Ok "/portfolio/weights OK"
    $portfolioData.allocations = Invoke-JsonGet -url "$BaseUrl/portfolio/allocations" -savePath "$OutputDir/allocations.json"
    Write-Ok "/portfolio/allocations OK"
    $portfolioData.risk = Invoke-JsonGet -url "$BaseUrl/portfolio/risk" -savePath "$OutputDir/risk.json"
    Write-Ok "/portfolio/risk OK"
    $portfolioData.summary = Invoke-JsonGet -url "$BaseUrl/portfolio/summary" -savePath "$OutputDir/summary.json"
    Write-Ok "/portfolio/summary OK"
    $portfolioData.paperPnl = Invoke-JsonGet -url "$BaseUrl/portfolio/paper-pnl" -savePath "$OutputDir/paper_pnl_before_cycles.json"
    Write-Ok "/portfolio/paper-pnl OK"
    return $portfolioData
}

function Test-PortfolioConsistency($portfolioData) {
    Write-Section "4. Portfolio Consistency Checks"
    $expectedCount = Get-ArrayCount (Get-PropertyIfExists -obj $portfolioData.expectedReturns -name "items")
    if ($expectedCount -eq 0) { $expectedCount = Get-ArrayCount $portfolioData.expectedReturns }
    if ($expectedCount -ge 1) { Write-Ok "Expected returns are not empty ($expectedCount item(s))" } else { Write-WarnMsg "Expected returns item count could not be confirmed from generic structure" }

    $latestSummary = Get-LatestRecord $portfolioData.summary
    $latestRisk = Get-LatestRecord $portfolioData.risk
    $portfolioId = Get-PropertyIfExists -obj $latestSummary -name "portfolio_id"
    if ($null -eq $portfolioId) { $portfolioId = Get-PropertyIfExists -obj $latestRisk -name "portfolio_id" }

    $weightRows = Filter-RecordsByPortfolioId -obj $portfolioData.weights -portfolioId $portfolioId
    $riskRows = Filter-RecordsByPortfolioId -obj $portfolioData.risk -portfolioId $portfolioId
    $riskRow = Get-LatestRecord $riskRows
    if ($null -eq $riskRow) { $riskRow = $latestRisk }

    $weightSum = Sum-TargetWeights -weightsObj $weightRows
    if ($weightSum -gt 0) {
        Write-Host ("Computed target_weight sum: {0:N6}" -f $weightSum)
        Write-Ok "Weight sum derived from target_weight"
    } else {
        Write-WarnMsg "Could not derive target_weight sum"
    }

    $gross = Get-PropertyIfExists -obj $riskRow -name "gross_exposure"
    $net = Get-PropertyIfExists -obj $riskRow -name "net_exposure"
    $concentration = Get-PropertyIfExists -obj $riskRow -name "concentration_top_weight"

    if ($null -ne $gross) {
        Write-Ok "gross_exposure found: $gross"
        if ($weightSum -gt 0) {
            $delta = [math]::Abs([double]$gross - [double]$weightSum)
            Assert-True ($delta -lt 0.0001) "gross_exposure and target_weight sum mismatch"
            Write-Ok "gross_exposure matches target_weight sum"
        }
    } else {
        Write-WarnMsg "gross_exposure not found"
    }

    if ($null -ne $net) { Write-Ok "net_exposure found: $net" } else { Write-WarnMsg "net_exposure not found" }
    if ($null -ne $concentration) { Write-Ok "concentration_top_weight found: $concentration" } else { Write-WarnMsg "concentration_top_weight not found" }

    $summaryPortfolioId = Get-PropertyIfExists -obj $latestSummary -name "portfolio_id"
    if ($null -ne $summaryPortfolioId) { Write-Ok "portfolio summary contains portfolio_id" } else { Write-WarnMsg "portfolio summary missing portfolio_id" }
}

function Test-RunnerStatus {
    Write-Section "5. Runner Status"
    $data = Invoke-JsonGet -url "$BaseUrl/runner/status" -savePath "$OutputDir/runner_status_before_cycles.json"
    Write-Ok "/runner/status OK"
    return $data
}

function Get-PnlFingerprint($obj) {
    if ($null -eq $obj) { return "" }
    return ($obj | ConvertTo-Json -Depth 30 -Compress)
}

function Run-Cycles {
    Write-Section "6. Runner Cycles"
    $beforeStatus = Invoke-JsonGet -url "$BaseUrl/runner/status" -savePath "$OutputDir/runner_status_cycle_start.json"
    $beforeCycleCount = Get-PropertyIfExists -obj $beforeStatus -name "cycle_count"
    $beforePnl = Invoke-JsonGet -url "$BaseUrl/portfolio/paper-pnl" -savePath "$OutputDir/paper_pnl_cycle_start.json"
    $beforeFingerprint = Get-PnlFingerprint -obj $beforePnl

    for ($i = 1; $i -le $RunCycleCount; $i++) {
        Invoke-JsonPost -url "$BaseUrl/runner/run-cycle" -savePath "$OutputDir/run_cycle_$i.json" | Out-Null
        Write-Ok "/runner/run-cycle executed ($i/$RunCycleCount)"
        Start-Sleep -Milliseconds 300
    }

    $afterStatus = Invoke-JsonGet -url "$BaseUrl/runner/status" -savePath "$OutputDir/runner_status_after_cycles.json"
    $afterCycleCount = Get-PropertyIfExists -obj $afterStatus -name "cycle_count"
    if ($null -ne $beforeCycleCount -and $null -ne $afterCycleCount) {
        Assert-True ($afterCycleCount -ge ($beforeCycleCount + $RunCycleCount)) "runner cycle_count did not advance as expected"
        Write-Ok "runner cycle_count advanced from $beforeCycleCount to $afterCycleCount"
    } else {
        Write-WarnMsg "Could not validate cycle_count numerically from runner status payload"
    }

    $afterPnl = Invoke-JsonGet -url "$BaseUrl/portfolio/paper-pnl" -savePath "$OutputDir/paper_pnl_after_cycles.json"
    $afterFingerprint = Get-PnlFingerprint -obj $afterPnl
    if ($beforeFingerprint -ne $afterFingerprint) { Write-Ok "paper-pnl changed after run-cycle executions" }
    else { Write-WarnMsg "paper-pnl did not visibly change after run cycles. This may be acceptable depending on implementation." }
}

function Test-StateRecoveryHint {
    Write-Section "7. State Recovery Manual Step"
@"
State recovery manual checklist
- Container restarts cleanly
- /runner/status returns successfully after restart
- /portfolio/paper-pnl still has prior state or expected persisted values
- No import/db/init errors appear in docker logs

Manual commands:
docker compose down
docker compose up
powershell -ExecutionPolicy Bypass -File .\scripts\check_phasec.ps1 -SkipPytest
"@ | Out-File -FilePath "$OutputDir/state_recovery_manual_checklist.txt" -Encoding utf8
    Write-Ok "State recovery manual checklist saved"
}

function Write-Summary {
    Write-Section "8. Summary"
    Write-Ok "PhaseC automated checks completed"
    Write-Host "Artifacts saved to: $OutputDir"
    Get-ChildItem $OutputDir | Select-Object Name, Length | Format-Table -AutoSize
}

try {
    Write-Section "PhaseC Automated Verification"
    Write-Host "BaseUrl      : $BaseUrl"
    Write-Host "OutputDir    : $OutputDir"
    Write-Host "RunCycleCount: $RunCycleCount"
    Write-Host "SkipPytest   : $SkipPytest"
    Write-Host "StartLocalApi: $StartLocalApi"

    if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null }

    Ensure-Pytest
    $apiJob = Start-ApiIfNeeded
    Test-Health
    Test-RunOnce
    $portfolioData = Test-PortfolioEndpoints
    Test-PortfolioConsistency -portfolioData $portfolioData
    Test-RunnerStatus | Out-Null
    Run-Cycles
    Test-StateRecoveryHint
    Write-Summary
}
catch {
    Write-Section "FAILED"
    Write-Ng $_.Exception.Message
    Write-Host $_.ScriptStackTrace
    exit 1
}
finally {
    Cleanup-ApiJob -Job $apiJob
}
