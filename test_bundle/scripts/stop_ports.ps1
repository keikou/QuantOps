param(
  [int[]]$Ports = @(),
  [string]$StatePath = "",
  [string[]]$CommandPatterns = @()
)

$ErrorActionPreference = "Stop"

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

  if (-not $Ports -or $Ports.Count -eq 0) {
    return
  }

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

function Stop-CommandPatternProcesses {
  param([string[]]$Patterns)

  if (-not $Patterns -or $Patterns.Count -eq 0) {
    return
  }

  try {
    $candidates = Get-CimInstance Win32_Process -ErrorAction Stop
  }
  catch {
    return
  }

  $matchedIds = @()
  foreach ($candidate in $candidates) {
    $commandLine = [string]$candidate.CommandLine
    if (-not $commandLine) {
      continue
    }
    foreach ($pattern in $Patterns) {
      if ($pattern -and $commandLine -like "*$pattern*") {
        $matchedIds += [int]$candidate.ProcessId
        break
      }
    }
  }

  foreach ($matchedId in ($matchedIds | Select-Object -Unique)) {
    try {
      Stop-Process -Id $matchedId -Force -ErrorAction Stop
    }
    catch {
    }
  }
}

$rootIds = @()
if ($StatePath -and (Test-Path $StatePath)) {
  try {
    $state = Get-Content $StatePath -Raw | ConvertFrom-Json
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
Stop-ListenerProcesses -Ports $Ports
Stop-CommandPatternProcesses -Patterns $CommandPatterns

if ($StatePath -and (Test-Path $StatePath)) {
  Remove-Item $StatePath -Force
}
