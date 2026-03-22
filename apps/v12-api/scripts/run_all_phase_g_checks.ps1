Write-Host 'Running all PhaseG verification scripts...'
python -m pytest tests/test_phaseg_api.py tests/test_phaseg_sprint1_api.py tests/test_phaseg_sprint2_api.py tests/test_phaseg_sprint3_api.py tests/test_api.py -q
