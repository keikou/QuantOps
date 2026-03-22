param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$RunCycleCount = 3,
    [switch]$StartLocalApi
)
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& powershell -ExecutionPolicy Bypass -File "$scriptDir/check_phased.ps1" -BaseUrl $BaseUrl -RunCycleCount $RunCycleCount $(if($StartLocalApi){'-StartLocalApi'})
if ($LASTEXITCODE -ne 0) { throw 'check_phased.ps1 failed.' }
