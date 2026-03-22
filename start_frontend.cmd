@echo off
cd /d %~dp0\apps\quantops-frontend

echo ==== QuantOps Frontend ====
if not exist node_modules (
    npm install
    if errorlevel 1 goto :error
)

npm run dev
goto :end

:error
echo.
echo [ERROR] Frontend startup failed.
pause

:end
pause