param(
  [switch]$CleanFirst
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")
Set-Location $RepoRoot

$env:NO_PAUSE = "1"
$targetPorts = @(8000, 8010, 3000)
$logDir = Join-Path $RepoRoot "test_bundle\artifacts\recheck_dev_logs"
$statePath = Join-Path $RepoRoot "test_bundle\artifacts\local_stack_state.json"
$logStatePath = Join-Path $logDir "pids.json"

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

function Get-StateProcessIds {
  param([string[]]$Paths)

  $ids = @()
  foreach ($path in $Paths) {
    if (-not (Test-Path $path)) {
      continue
    }
    try {
      $state = Get-Content $path -Raw | ConvertFrom-Json
      foreach ($item in @($state)) {
        if ($item.Id) {
          $ids += [int]$item.Id
        }
      }
    }
    catch {
    }
  }
  return $ids | Select-Object -Unique
}

function Start-LoggedCmd {
  param(
    [string]$Name,
    [string]$Command
  )

  Write-Host ("Starting {0}" -f $Name)
  $process = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", $Command `
    -WorkingDirectory $RepoRoot `
    -WindowStyle Hidden `
    -PassThru

  return $process
}

function Wait-ForHttpOk {
  param(
    [string]$Name,
    [string]$Url,
    [int]$TimeoutSec = 180
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  $lastError = $null

  while ((Get-Date) -lt $deadline) {
    try {
      $response = Invoke-WebRequest -Uri $Url -TimeoutSec 20 -UseBasicParsing
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

if ($CleanFirst) {
  $knownRootIds = Get-StateProcessIds -Paths @($statePath, $logStatePath)
  Stop-ProcessTree -RootIds $knownRootIds
  Stop-ListenerProcesses -Ports $targetPorts
  Start-Sleep -Seconds 1
}

New-Item -ItemType Directory -Path $logDir -Force | Out-Null
foreach ($fileName in @("v12.log", "quantops.log", "frontend-dev.log", "pids.json")) {
  $target = Join-Path $logDir $fileName
  if (Test-Path $target) {
    try {
      Remove-Item $target -Force -ErrorAction Stop
    }
    catch {
      try {
        Clear-Content -Path $target -Force -ErrorAction Stop
      }
      catch {
        throw ("Failed to reset log file {0}: {1}" -f $target, $_.Exception.Message)
      }
    }
  }
}

$v12Log = Join-Path $logDir "v12.log"
$quantopsLog = Join-Path $logDir "quantops.log"
$frontendLog = Join-Path $logDir "frontend-dev.log"

$started = @()
$started += Start-LoggedCmd -Name "V12 API" -Command "start_v12_api.cmd > `"$v12Log`" 2>&1"
Wait-ForHttpOk -Name "V12 Health" -Url "http://127.0.0.1:8000/system/health"

$started += Start-LoggedCmd -Name "QuantOps API" -Command "start_quantops_api.cmd > `"$quantopsLog`" 2>&1"
Wait-ForHttpOk -Name "QuantOps Health" -Url "http://127.0.0.1:8010/api/v1/health"

$started += Start-LoggedCmd -Name "QuantOps Frontend (dev)" -Command "start_frontend.cmd > `"$frontendLog`" 2>&1"
Wait-ForHttpOk -Name "Frontend Home" -Url "http://127.0.0.1:3000/"

$started | Select-Object Id, ProcessName | ConvertTo-Json | Set-Content -Path $statePath -Encoding UTF8
$started | Select-Object Id, ProcessName | ConvertTo-Json | Set-Content -Path $logStatePath -Encoding UTF8
Write-Host ("Logs: {0}" -f $logDir)
Write-Host ("State file: {0}" -f $statePath)
