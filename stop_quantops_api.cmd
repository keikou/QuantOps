@echo off
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File "%~dp0test_bundle\scripts\stop_ports.ps1" -Ports 8010 -CommandPatterns "apps\quantops-api\.venv\Scripts\python.exe","app.main:app --host 0.0.0.0 --port 8010","call start_quantops_api.cmd"
if errorlevel 1 (
    echo [ERROR] QuantOps API stop failed.
    exit /b 1
)
