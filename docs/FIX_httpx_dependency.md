# Fix: httpx dependency

QuantOps API uses `httpx` in:

app/clients/v12_client.py

Previous runtime bundle missed this dependency, causing:

ModuleNotFoundError: No module named 'httpx'

This version adds:

httpx

to:

- apps/quantops-api/requirements.txt
- apps/v12-api/requirements.txt
