@echo off
cd /d %~dp0\apps\quantops-api

echo ==== QuantOps API ====
if not exist .venv (
    python -m venv .venv
)

set VENV_PYTHON=%CD%\.venv\Scripts\python.exe
if not exist "%VENV_PYTHON%" goto :error

if not exist .venv\Scripts\pip.exe (
    "%VENV_PYTHON%" -m ensurepip --upgrade
    if errorlevel 1 goto :error
)

set V12_BASE_URL=http://127.0.0.1:8000
set V12_MOCK_MODE=false
set QUANTOPS_DB_PATH=./data/quantops.duckdb

echo V12_BASE_URL=%V12_BASE_URL%
echo V12_MOCK_MODE=%V12_MOCK_MODE%
echo QUANTOPS_DB_PATH=%QUANTOPS_DB_PATH%



if not exist .venv\installed.flag (
    "%VENV_PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
    echo done > .venv\installed.flag
)

"%VENV_PYTHON%" -m app.db.migrate
if errorlevel 1 goto :error

"%VENV_PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port 8010
goto :end

:error
echo.
echo [ERROR] QuantOps API startup failed.
if "%NO_PAUSE%"=="1" goto :end
pause

:end
if "%NO_PAUSE%"=="1" goto :eof
pause
