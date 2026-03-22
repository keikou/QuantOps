param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$RunCycleCount = 3,
    [switch]$SkipPytest,
    [switch]$StartLocalApi
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$forwardArgs = @(
    "-ExecutionPolicy", "Bypass",
    "-File", "$scriptDir/check_phasec.ps1",
    "-BaseUrl", "$BaseUrl",
    "-RunCycleCount", "$RunCycleCount"
)
if ($SkipPytest) { $forwardArgs += "-SkipPytest" }
if ($StartLocalApi) { $forwardArgs += "-StartLocalApi" }

& powershell @forwardArgs
exit $LASTEXITCODE
