$base = "http://localhost:8010/api/v1"

Write-Host ""
Write-Host "QuantOps Alert Root Cause Probe"
Write-Host "================================"
Write-Host ""

$risk1 = Invoke-RestMethod "$base/risk/snapshot"
$alerts = Invoke-RestMethod "$base/alerts"
$scheduler = Invoke-RestMethod "$base/scheduler/jobs"

Start-Sleep -Seconds 3

$risk2 = Invoke-RestMethod "$base/risk/snapshot"

Write-Host "[1] Risk snapshot"
$risk1 | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "[2] drawdown / limit"
Write-Host "drawdown = $($risk1.drawdown)"
Write-Host "limit.drawdown = $($risk1.risk_limit.drawdown)"

if ($risk1.drawdown -gt $risk1.risk_limit.drawdown) {
    Write-Host "[INFO] drawdown breach condition met"
} else {
    Write-Host "[INFO] drawdown breach condition NOT met"
}

Write-Host ""
Write-Host "[3] alert / trading state"
Write-Host "alert_state   = $($risk1.alert_state)"
Write-Host "alert         = $($risk1.alert)"
Write-Host "kill_switch   = $($risk1.kill_switch)"
Write-Host "trading_state = $($risk1.trading_state)"

if ($risk1.kill_switch -eq "triggered" -and $risk1.trading_state -eq "running") {
    Write-Host "[FAIL] kill_switch and trading_state inconsistent"
} else {
    Write-Host "[PASS] kill_switch and trading_state look consistent"
}

Write-Host ""
Write-Host "[4] alerts count"

$alertCount = 0
if ($alerts -is [System.Array]) {
    $alertCount = $alerts.Count
} elseif ($alerts.items) {
    $alertCount = $alerts.items.Count
} elseif ($alerts.alerts) {
    $alertCount = $alerts.alerts.Count
}

Write-Host "alerts_count = $alertCount"

if (($risk1.alert_state -eq "breach" -or $risk1.alert -eq "breach") -and $alertCount -eq 0) {
    Write-Host "[FAIL] breach exists but alerts are empty"
}

Write-Host ""
Write-Host "[5] scheduler jobs"

$jobs = @()
if ($scheduler -is [System.Array]) {
    $jobs = $scheduler
} elseif ($scheduler.items) {
    $jobs = $scheduler.items
} elseif ($scheduler.jobs) {
    $jobs = $scheduler.jobs
}

$alertJobs = @()
foreach ($j in $jobs) {
    $name = ""
    if ($j.job_id) { $name = $j.job_id }
    elseif ($j.id) { $name = $j.id }
    elseif ($j.name) { $name = $j.name }

    if ($name.ToLower().Contains("alert")) {
        $alertJobs += $name
    }
}

if ($alertJobs.Count -eq 0) {
    Write-Host "[FAIL] no alert-related scheduler jobs found"
} else {
    Write-Host "[INFO] alert jobs found:"
    $alertJobs
}

Write-Host ""
Write-Host "[6] stale snapshot"
Write-Host "as_of_1 = $($risk1.as_of)"
Write-Host "as_of_2 = $($risk2.as_of)"

if ($risk1.as_of -eq $risk2.as_of) {
    Write-Host "[WARN] risk snapshot as_of did not change"
} else {
    Write-Host "[PASS] risk snapshot as_of changed"
}