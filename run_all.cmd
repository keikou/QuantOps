@echo off
cd /d %~dp0

start "V12 API" cmd /k start_v12_api.cmd
start "QuantOps API" cmd /k start_quantops_api.cmd
start "QuantOps Frontend" cmd /k start_frontend.cmd

echo All startup windows opened.
pause