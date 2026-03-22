param(
  [int]$StartupTimeoutSec = 180,
  [int]$RequestTimeoutSec = 20
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")
Set-Location $RepoRoot

$env:NO_PAUSE = "1"

$startedProcesses = @()
$targetPorts = @(8000, 8010, 3000)

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

try {
  $v12 = Start-ServiceScript -Name "V12 API" -ScriptPath "start_v12_api.cmd"
  $quantops = Start-ServiceScript -Name "QuantOps API" -ScriptPath "start_quantops_api.cmd"
  $frontend = Start-ServiceScript -Name "QuantOps Frontend" -ScriptPath "start_frontend.cmd"

  Wait-ForHttpOk -Name "V12 Health" -Url "http://127.0.0.1:8000/system/health" -TimeoutSec $StartupTimeoutSec
  Wait-ForHttpOk -Name "QuantOps Health" -Url "http://127.0.0.1:8010/api/v1/health" -TimeoutSec $StartupTimeoutSec
  Wait-ForHttpOk -Name "Frontend Home" -Url "http://127.0.0.1:3000/" -TimeoutSec $StartupTimeoutSec

  Wait-ForHttpOk -Name "QuantOps Overview" -Url "http://127.0.0.1:8010/api/v1/dashboard/overview" -TimeoutSec $RequestTimeoutSec

  Write-Host ""
  Write-Host "Local startup smoke passed."
}
finally {
  Write-Host ""
  Write-Host "Stopping local startup smoke processes..."
  Stop-ListenerProcesses -Ports $targetPorts
  Stop-ProcessTree -RootIds ($startedProcesses | ForEach-Object { $_.Id })
}
