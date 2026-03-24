@echo off
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File "%~dp0test_bundle\scripts\start_local_stack.ps1" -CleanFirst
if errorlevel 1 (
    echo [ERROR] Local dev stack startup failed.
    exit /b 1
)
