$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Push-Location "$root/apps/v12-api"
pytest -q tests/test_sprint5_runtime_api.py tests/test_sprint5c_api.py tests/test_sprint5d_api.py tests/test_sprint5_integrated_api.py
Pop-Location
Push-Location "$root/apps/quantops-api"
pytest -q app/tests/test_sprint5c_quantops_api.py app/tests/test_sprint5d_quantops_api.py app/tests/test_sprint5_integrated_quantops_api.py
Pop-Location
