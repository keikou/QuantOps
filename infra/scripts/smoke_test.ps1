$ErrorActionPreference = "Stop"

$v12 = Invoke-WebRequest -UseBasicParsing http://localhost:8000/health
$qops = Invoke-WebRequest -UseBasicParsing http://localhost:8010/api/v1/health
$docs = Invoke-WebRequest -UseBasicParsing http://localhost:8010/docs

Write-Host "V12:" $v12.StatusCode
Write-Host "QuantOps:" $qops.StatusCode
Write-Host "Docs:" $docs.StatusCode
