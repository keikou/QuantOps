# Fix: quantops-worker import path

Worker originally ran:

python app/worker.py

This caused:

ModuleNotFoundError: No module named 'app'

Because Python executed worker as a standalone script.

Fix applied:

python -m app.worker

This ensures the `app` package is resolved correctly inside the container.
