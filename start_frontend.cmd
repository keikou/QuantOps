@echo off
cd /d %~dp0\apps\quantops-frontend

echo ==== QuantOps Frontend ====
set QUANTOPS_API_BASE_URL=http://127.0.0.1:8010
if not exist node_modules (
    npm install
    if errorlevel 1 goto :error
)

npm run dev
goto :end

:error
echo.
echo [ERROR] Frontend startup failed.
if "%NO_PAUSE%"=="1" goto :end
pause

:end
if "%NO_PAUSE%"=="1" goto :eof
pause
