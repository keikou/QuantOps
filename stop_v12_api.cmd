@echo off
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File "%~dp0test_bundle\scripts\stop_ports.ps1" -Ports 8000 -CommandPatterns "apps\v12-api\.venv\Scripts\python.exe","ai_hedge_bot.api.app:app --host 0.0.0.0 --port 8000","call start_v12_api.cmd"
if errorlevel 1 (
    echo [ERROR] V12 API stop failed.
    exit /b 1
)
