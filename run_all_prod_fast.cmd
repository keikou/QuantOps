@echo off
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File "%~dp0test_bundle\scripts\start_local_stack_prod.ps1" -CleanFirst -SkipFrontendBuild -SkipQuantopsMigrate
if errorlevel 1 (
    echo [ERROR] Fast production stack startup failed.
    exit /b 1
)
