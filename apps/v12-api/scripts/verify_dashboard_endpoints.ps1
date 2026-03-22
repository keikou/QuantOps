Write-Host 'Verifying dashboard endpoints...'
python -m pytest tests/test_phaseg_sprint3_api.py -q -k dashboard
