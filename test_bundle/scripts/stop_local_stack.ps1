param()

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")
$targetPorts = @(8000, 8010, 3000)
$statePath = Join-Path $RepoRoot "test_bundle\artifacts\local_stack_state.json"

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

$rootIds = @()
if (Test-Path $statePath) {
  try {
    $state = Get-Content $statePath -Raw | ConvertFrom-Json
    foreach ($item in @($state)) {
      if ($item.Id) {
        $rootIds += [int]$item.Id
      }
    }
  }
  catch {
  }
}

Stop-ProcessTree -RootIds $rootIds
Stop-ListenerProcesses -Ports $targetPorts

if (Test-Path $statePath) {
  Remove-Item $statePath -Force
}
