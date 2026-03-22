param(
    [switch]$StartLocalApi,
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$script = Join-Path $PSScriptRoot 'check_phaseh_sprint2.ps1'
$args = @('-ExecutionPolicy','Bypass','-File',$script,'-BaseUrl',$BaseUrl)
if ($StartLocalApi) {
    $args += '-StartLocalApi'
}

powershell @args
