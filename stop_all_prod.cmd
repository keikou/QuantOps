@echo off
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File "%~dp0test_bundle\scripts\stop_local_stack.ps1"
if errorlevel 1 (
    echo [ERROR] Production stack stop failed.
    exit /b 1
)
