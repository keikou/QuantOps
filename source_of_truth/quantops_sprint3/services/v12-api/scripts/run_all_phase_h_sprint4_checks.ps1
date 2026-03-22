param(
    [switch]$StartLocalApi
)
$scriptPath = Join-Path $PSScriptRoot 'check_phaseh_sprint4.ps1'
if ($StartLocalApi) {
    powershell -ExecutionPolicy Bypass -File $scriptPath -StartLocalApi
} else {
    powershell -ExecutionPolicy Bypass -File $scriptPath
}
