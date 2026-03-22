# QuantOps Sprint1 API

FastAPI backend for the Sprint1 control plane.

## Endpoints
- `GET /api/v1/dashboard/overview`
- `GET /api/v1/dashboard/system-health`
- `GET /api/v1/portfolio/overview`
- `GET /api/v1/portfolio/positions`
- `GET /api/v1/scheduler/jobs`
- `POST /api/v1/scheduler/jobs`
- `POST /api/v1/scheduler/run/{job_id}`
- `GET /api/v1/risk/snapshot`
- `POST /api/v1/risk/refresh`
- `POST /api/v1/control/rebalance`

Run locally:

```bash
python -m app.db.migrate
uvicorn app.main:app --reload --port 8001
```


## Docker one-step
```bash
docker compose up --build
```

PowerShell validation:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_all_checks.ps1
```
