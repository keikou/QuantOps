# PhaseH Sprint2

Scope:
- Experiment Tracker
- Dataset Registry
- Feature Registry
- Validation Registry
- Model Registry
- DuckDB persistence
- FastAPI routes
- pytest and PowerShell verification

Key commands:

```powershell
python -m pytest -q
powershell -ExecutionPolicy Bypass -File .\scripts\check_phaseh_sprint2.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\check_phaseh_sprint2.ps1 -StartLocalApi
docker compose up --build
```
