param(
    [string]$ComposeFile = "docker-compose.yml",
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$RunCycleCount = 3,
    [string]$OutputDir = "runtime/verification_logs"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

function Wait-Health {
    param([string]$Url)
    for($i=0; $i -lt 60; $i++){
        Start-Sleep -Seconds 2
        try {
            $health = Invoke-RestMethod -Method GET -Uri "$Url/health" -TimeoutSec 5
            if($health.status -eq 'ok'){ return $true }
        } catch {}
    }
    return $false
}

function Save-DockerLogs {
    param([string]$DestinationFile)
    try {
        $containers = docker compose -f $ComposeFile ps -q
        if ($containers) {
            docker compose -f $ComposeFile logs --no-color | Set-Content -Path $DestinationFile -Encoding UTF8
        }
    } catch {}
}

$resolvedOutDir = if ([System.IO.Path]::IsPathRooted($OutputDir)) { $OutputDir } else { Join-Path $projectRoot $OutputDir }
New-Item -ItemType Directory -Force -Path $resolvedOutDir | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$dockerLogFile = Join-Path $resolvedOutDir ("docker_compose_" + $timestamp + ".log")

try {
    docker compose -f $ComposeFile down --remove-orphans
    if ($LASTEXITCODE -ne 0) { throw 'docker compose down failed.' }
    docker compose -f $ComposeFile up -d --build
    if ($LASTEXITCODE -ne 0) { throw 'docker compose up failed.' }
    if (-not (Wait-Health -Url $BaseUrl)) { throw 'Docker API health check timed out.' }
    & powershell -ExecutionPolicy Bypass -File "$scriptDir/verify_phase_d_cycle.ps1" -BaseUrl $BaseUrl -RunCycleCount $RunCycleCount -OutputDir $OutputDir
    if ($LASTEXITCODE -ne 0) { throw 'verify_phase_d_cycle.ps1 failed after docker startup.' }
    Save-DockerLogs -DestinationFile $dockerLogFile
    Write-Host ("Docker one-command verification passed. docker_log={0}" -f $dockerLogFile) -ForegroundColor Green
}
finally {
    Save-DockerLogs -DestinationFile $dockerLogFile
    docker compose -f $ComposeFile down --remove-orphans
}
