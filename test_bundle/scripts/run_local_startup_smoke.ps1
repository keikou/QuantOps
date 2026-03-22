param(
  [int]$StartupTimeoutSec = 180,
  [int]$RequestTimeoutSec = 20
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")
Set-Location $RepoRoot

$env:NO_PAUSE = "1"
$artifactRoot = Join-Path $RepoRoot "test_bundle\artifacts\runtime_diagnostics"

$startedProcesses = @()
$targetPorts = @(8000, 8010, 3000)
$repoRootText = [string]$RepoRoot

function Get-DescendantProcessIds {
  param([int]$ParentId)

  $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ParentId" -ErrorAction SilentlyContinue
  $ids = @()
  foreach ($child in $children) {
    $ids += $child.ProcessId
    $ids += Get-DescendantProcessIds -ParentId $child.ProcessId
  }
  return $ids
}

function Stop-ProcessTree {
  param([int[]]$RootIds)

  $allIds = New-Object System.Collections.Generic.List[int]
  foreach ($rootId in $RootIds) {
    if (-not $rootId) {
      continue
    }
    $allIds.Add($rootId)
    foreach ($childId in (Get-DescendantProcessIds -ParentId $rootId)) {
      $allIds.Add($childId)
    }
  }

  $ordered = $allIds | Select-Object -Unique | Sort-Object -Descending
  foreach ($processId in $ordered) {
    try {
      Stop-Process -Id $processId -Force -ErrorAction Stop
    }
    catch {
    }
  }
}

function Stop-ListenerProcesses {
  param([int[]]$Ports)

  try {
    $listenerIds = Get-NetTCPConnection -State Listen -ErrorAction Stop |
      Where-Object { $_.LocalPort -in $Ports } |
      Select-Object -ExpandProperty OwningProcess -Unique
  }
  catch {
    $listenerIds = @()
  }

  foreach ($listenerId in $listenerIds) {
    try {
      Stop-Process -Id $listenerId -Force -ErrorAction Stop
    }
    catch {
    }
  }
}

function Stop-RepoRuntimeProcesses {
  param([string]$RepoPath)

  $repoPathLower = $RepoPath.ToLowerInvariant()
  $candidates = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
      ($_.Name -in @("python.exe", "node.exe", "cmd.exe")) -and
      ($_.CommandLine -ne $null) -and
      ($_.CommandLine.ToLowerInvariant().Contains($repoPathLower))
    } |
    Select-Object -ExpandProperty ProcessId -Unique

  foreach ($candidateId in $candidates) {
    try {
      Stop-Process -Id $candidateId -Force -ErrorAction Stop
    }
    catch {
    }
  }
}

function Start-ServiceScript {
  param(
    [string]$Name,
    [string]$ScriptPath
  )

  Write-Host ("Starting {0} with {1}" -f $Name, $ScriptPath)
  $process = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", $ScriptPath `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Hidden `
    -PassThru

  $script:startedProcesses += $process
  return $process
}

function Wait-ForHttpOk {
  param(
    [string]$Name,
    [string]$Url,
    [int]$TimeoutSec
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  $lastError = $null

  while ((Get-Date) -lt $deadline) {
    try {
      $response = Invoke-WebRequest -Uri $Url -TimeoutSec $RequestTimeoutSec -UseBasicParsing
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
        Write-Host ("OK {0}: {1} ({2})" -f $Name, $Url, $response.StatusCode)
        return
      }
      $lastError = "Unexpected status code: $($response.StatusCode)"
    }
    catch {
      $lastError = $_.Exception.Message
    }
    Start-Sleep -Seconds 2
  }

  throw ("Timeout waiting for {0} at {1}. Last error: {2}" -f $Name, $Url, $lastError)
}

function Get-Json {
  param(
    [string]$Url,
    [string]$Method = "GET",
    [object]$Body = $null
  )

  if ($null -ne $Body) {
    $jsonBody = $Body | ConvertTo-Json -Depth 8
    return Invoke-RestMethod -Uri $Url -Method $Method -TimeoutSec $RequestTimeoutSec -ContentType "application/json" -Body $jsonBody
  }

  return Invoke-RestMethod -Uri $Url -Method $Method -TimeoutSec $RequestTimeoutSec
}

function Assert-True {
  param(
    [bool]$Condition,
    [string]$Message
  )

  if (-not $Condition) {
    throw $Message
  }
}

function Write-RuntimeArtifactBundle {
  param(
    [string]$RunId,
    [object]$RunPayload,
    [object]$PlannerTruth,
    [object]$BridgeTruth,
    [object]$RuntimeEvents
  )

  if (-not (Test-Path $artifactRoot)) {
    New-Item -ItemType Directory -Path $artifactRoot -Force | Out-Null
  }

  $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $artifactPath = Join-Path $artifactRoot ("{0}_{1}.json" -f $timestamp, $RunId)
  $bundle = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    run_id = $RunId
    run_payload = $RunPayload
    planner_truth = $PlannerTruth
    bridge_truth = $BridgeTruth
    runtime_events = $RuntimeEvents.items
  }
  $bundle | ConvertTo-Json -Depth 12 | Set-Content -Path $artifactPath -Encoding UTF8
  Write-Host ("Artifact bundle: {0}" -f $artifactPath)
}

try {
  Stop-RepoRuntimeProcesses -RepoPath $repoRootText
  Stop-ListenerProcesses -Ports $targetPorts

  $v12 = Start-ServiceScript -Name "V12 API" -ScriptPath "start_v12_api.cmd"
  $quantops = Start-ServiceScript -Name "QuantOps API" -ScriptPath "start_quantops_api.cmd"
  $frontend = Start-ServiceScript -Name "QuantOps Frontend" -ScriptPath "start_frontend.cmd"

  Wait-ForHttpOk -Name "V12 Health" -Url "http://127.0.0.1:8000/system/health" -TimeoutSec $StartupTimeoutSec
  Wait-ForHttpOk -Name "QuantOps Health" -Url "http://127.0.0.1:8010/api/v1/health" -TimeoutSec $StartupTimeoutSec
  Wait-ForHttpOk -Name "Frontend Home" -Url "http://127.0.0.1:3000/" -TimeoutSec $StartupTimeoutSec

  Wait-ForHttpOk -Name "QuantOps Overview" -Url "http://127.0.0.1:8010/api/v1/dashboard/overview" -TimeoutSec $RequestTimeoutSec

  $null = Get-Json -Url "http://127.0.0.1:8000/runtime/resume" -Method "POST"
  $runPayload = Get-Json -Url "http://127.0.0.1:8000/runtime/run-once?mode=paper" -Method "POST"
  Assert-True -Condition ($runPayload.status -eq "ok") -Message "Runtime smoke cycle did not complete successfully."
  $runId = [string]$runPayload.run_id
  Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($runId)) -Message "Runtime smoke cycle did not return a run_id."

  $runtimeEvents = Get-Json -Url "http://127.0.0.1:8000/runtime/events/latest?limit=100"
  $runEvents = @($runtimeEvents.items | Where-Object { $_.run_id -eq $runId })
  $eventTypes = @($runEvents | ForEach-Object { [string]$_.event_type })
  Assert-True -Condition ($eventTypes -contains "cycle_started") -Message "Runtime smoke did not emit cycle_started."
  Assert-True -Condition ($eventTypes -contains "cycle_completed") -Message "Runtime smoke did not emit cycle_completed."

  $plannerTruth = Get-Json -Url ("http://127.0.0.1:8000/execution/plans/by-run/{0}" -f $runId)
  $bridgeTruth = Get-Json -Url ("http://127.0.0.1:8000/execution/bridge/by-run/{0}" -f $runId)

  Assert-True -Condition ($plannerTruth.run_id -eq $runId) -Message "Planner truth run_id mismatch."
  Assert-True -Condition ($bridgeTruth.run_id -eq $runId) -Message "Bridge diagnostics run_id mismatch."
  Assert-True -Condition ($bridgeTruth.event_chain_complete -eq $true) -Message "Bridge diagnostics did not report a complete event chain."
  Assert-True -Condition (@("no_decision","planned_blocked","planned_not_submitted","submitted_no_fill","filled","failed") -contains [string]$bridgeTruth.bridge_state) -Message "Bridge diagnostics returned an unexpected bridge_state."
  if ([int]$bridgeTruth.submitted_count -eq 0) {
    Assert-True -Condition (-not [string]::IsNullOrWhiteSpace([string]$bridgeTruth.zero_submit_reason_code)) -Message "Zero-submit bridge diagnostics lacked a reason code."
  }

  Write-RuntimeArtifactBundle -RunId $runId -RunPayload $runPayload -PlannerTruth $plannerTruth -BridgeTruth $bridgeTruth -RuntimeEvents $runtimeEvents

  Write-Host ""
  Write-Host "Local startup smoke passed."
}
finally {
  Write-Host ""
  Write-Host "Stopping local startup smoke processes..."
  Stop-ListenerProcesses -Ports $targetPorts
  Stop-ProcessTree -RootIds ($startedProcesses | ForEach-Object { $_.Id })
}
