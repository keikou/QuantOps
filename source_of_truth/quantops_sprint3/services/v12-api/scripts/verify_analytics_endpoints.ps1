Write-Host 'Verifying analytics endpoints...'
python -m pytest tests/test_phaseg_sprint3_api.py -q -k analytics
