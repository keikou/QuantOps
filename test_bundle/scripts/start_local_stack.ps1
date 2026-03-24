param(
  [switch]$CleanFirst
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")
Set-Location $RepoRoot

$env:NO_PAUSE = "1"
$targetPorts = @(8000, 8010, 3000)
$statePath = Join-Path $RepoRoot "test_bundle\artifacts\local_stack_state.json"

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
  Stop-ListenerProcesses -Ports $targetPorts
}

$started = @(
  Start-ServiceScript -Name "V12 API" -ScriptPath "start_v12_api.cmd"
  Start-ServiceScript -Name "QuantOps API" -ScriptPath "start_quantops_api.cmd"
  Start-ServiceScript -Name "QuantOps Frontend" -ScriptPath "start_frontend.cmd"
)

Wait-ForHttpOk -Name "V12 Health" -Url "http://127.0.0.1:8000/system/health"
Wait-ForHttpOk -Name "QuantOps Health" -Url "http://127.0.0.1:8010/api/v1/health"
Wait-ForHttpOk -Name "Frontend Home" -Url "http://127.0.0.1:3000/"

$started | Select-Object Id, ProcessName | ConvertTo-Json | Set-Content -Path $statePath -Encoding UTF8
Write-Host ("State file: {0}" -f $statePath)
