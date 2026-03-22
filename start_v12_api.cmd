@echo off
cd /d %~dp0\apps\v12-api

echo ==== V12 API ====
if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate.bat
if errorlevel 1 goto :error

if not exist .venv\installed.flag (
    pip install -r requirements.txt
    if errorlevel 1 goto :error
    echo done > .venv\installed.flag
)

set ENABLE_STARTUP_PAPER_LOOP=true
set PAPER_CYCLE_INTERVAL_SEC=60

echo ENABLE_STARTUP_PAPER_LOOP=%ENABLE_STARTUP_PAPER_LOOP%
echo PAPER_CYCLE_INTERVAL_SEC=%PAPER_CYCLE_INTERVAL_SEC%

python -m uvicorn ai_hedge_bot.api.app:app --host 0.0.0.0 --port 8000
goto :end

:error
echo.
echo [ERROR] V12 API startup failed.
pause

:end
pause