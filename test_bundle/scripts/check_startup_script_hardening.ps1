param()

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")
Set-Location $RepoRoot

function Assert-Pattern {
  param(
    [string]$Content,
    [string]$Pattern,
    [string]$Message
  )

  if ($Content -notmatch $Pattern) {
    throw $Message
  }
}

function Assert-NoPattern {
  param(
    [string]$Content,
    [string]$Pattern,
    [string]$Message
  )

  if ($Content -match $Pattern) {
    throw $Message
  }
}

$v12 = Get-Content "start_v12_api.cmd" -Raw
$quantops = Get-Content "start_quantops_api.cmd" -Raw
$frontend = Get-Content "start_frontend.cmd" -Raw

Assert-Pattern $v12 'python -m venv \.venv' 'start_v12_api.cmd must bootstrap a local venv with python -m venv.'
Assert-Pattern $v12 '"%VENV_PYTHON%" -m ensurepip --upgrade' 'start_v12_api.cmd must bootstrap pip with ensurepip via the local venv python.'
Assert-Pattern $v12 '"%VENV_PYTHON%" -m pip install -r requirements.txt' 'start_v12_api.cmd must install requirements with python -m pip from the local venv.'
Assert-NoPattern $v12 '"[^"]*\\Scripts\\pip\.exe"\s+-' 'start_v12_api.cmd must not invoke pip.exe directly.'

Assert-Pattern $quantops 'python -m venv \.venv' 'start_quantops_api.cmd must bootstrap a local venv with python -m venv.'
Assert-Pattern $quantops '"%VENV_PYTHON%" -m ensurepip --upgrade' 'start_quantops_api.cmd must bootstrap pip with ensurepip via the local venv python.'
Assert-Pattern $quantops '"%VENV_PYTHON%" -m pip install -r requirements.txt' 'start_quantops_api.cmd must install requirements with python -m pip from the local venv.'
Assert-Pattern $quantops 'set V12_BASE_URL=http://127\.0\.0\.1:8000' 'start_quantops_api.cmd must point to the local V12 service via 127.0.0.1.'
Assert-NoPattern $quantops '"[^"]*\\Scripts\\pip\.exe"\s+-' 'start_quantops_api.cmd must not invoke pip.exe directly.'
Assert-NoPattern $quantops 'uvicorn\.exe' 'start_quantops_api.cmd must not launch a stale uvicorn.exe shim.'

Assert-Pattern $frontend 'set QUANTOPS_API_BASE_URL=http://127\.0\.0\.1:8010' 'start_frontend.cmd must point to the local QuantOps API via 127.0.0.1.'

Write-Host "Startup script hardening checks passed."
