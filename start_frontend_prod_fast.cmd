@echo off
setlocal
set SKIP_BUILD=0
if /I "%~1"=="--skip-build" set SKIP_BUILD=1
if /I "%SKIP_FRONTEND_BUILD%"=="1" set SKIP_BUILD=1

cd /d %~dp0\apps\quantops-frontend

echo ==== QuantOps Frontend Production ====
set QUANTOPS_API_BASE_URL=http://127.0.0.1:8010


call npm run start
goto :end

:error
echo.
echo [ERROR] Frontend production startup failed.
if "%NO_PAUSE%"=="1" goto :end
pause

:end
if "%NO_PAUSE%"=="1" goto :eof
pause
