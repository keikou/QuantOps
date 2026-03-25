@echo off
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File "%~dp0test_bundle\scripts\stop_ports.ps1" -Ports 3000 -CommandPatterns "apps\quantops-frontend","next-server","next dev","next start","call start_frontend.cmd","call start_frontend_prod.cmd"
if errorlevel 1 (
    echo [ERROR] Frontend stop failed.
    exit /b 1
)
