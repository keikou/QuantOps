# Developer Startup And Verification

This document captures the current working local startup path for `Sprint6H-9.2.7.12`.

## Startup Order

Preferred order:

1. `start_v12_api.cmd`
2. `start_quantops_api.cmd`
3. `start_frontend.cmd`

Or run everything from the repo root:

```bat
run_all.cmd
```

## Ports

- V12 API: `8000`
- QuantOps API: `8010`
- QuantOps Frontend: `3000`

Core URLs:

- V12 health: `http://127.0.0.1:8000/system/health`
- QuantOps health: `http://127.0.0.1:8010/api/v1/health`
- QuantOps overview: `http://127.0.0.1:8010/api/v1/dashboard/overview`
- Frontend root: `http://127.0.0.1:3000/`

## Local Routing Rules

Local service-to-service calls should use `127.0.0.1`, not `localhost`.

Why:

- avoids IPv4/IPv6 resolution drift
- avoids slow or inconsistent localhost name resolution on some Windows setups
- matches the startup scripts and frontend proxy defaults already verified in this repo

## Startup Behavior

- `start_v12_api.cmd`
  - creates `apps/v12-api/.venv` if missing
  - bootstraps pip with `python -m ensurepip --upgrade`
  - installs dependencies with `python -m pip`
  - starts Uvicorn on `8000`
- `start_quantops_api.cmd`
  - creates `apps/quantops-api/.venv` if missing
  - bootstraps pip with `python -m ensurepip --upgrade`
  - installs dependencies with `python -m pip`
  - runs DB migration
  - starts Uvicorn on `8010`
- `start_frontend.cmd`
  - installs frontend dependencies when `node_modules` is missing
  - starts Next.js dev server on `3000`

For scripted smoke runs, set `NO_PAUSE=1` so the `.cmd` wrappers do not block on `pause`.

## Frontend Timeout Policy

The frontend uses a default API timeout of `8000ms`, with extended budgets for heavier local-dev routes:

- `/api/v1/dashboard/overview`: `35000ms`
- `/api/v1/analytics/equity-history`: `30000ms`
- `/api/v1/monitoring/system`: `25000ms`
- `/api/v1/scheduler/jobs`: `15000ms`
- `/api/v1/portfolio/positions`: `12000ms`
- `/api/v1/portfolio/overview`: `12000ms`

These budgets exist to prevent false timeout banners in Next.js dev mode while keeping normal routes on a smaller timeout.

## Verification Commands

Frontend production build:

```powershell
Set-Location apps/quantops-frontend
npm run build
```

QuantOps API regression packs:

```powershell
powershell -ExecutionPolicy Bypass -File test_bundle/scripts/run_quantops_api_regression_pack.ps1 -Pack all
```

Local startup smoke:

```powershell
powershell -ExecutionPolicy Bypass -File test_bundle/scripts/run_local_startup_smoke.ps1
```

The smoke script starts the local stack, probes the health endpoints above, validates `dashboard/overview`, and shuts the listeners down at the end so the next test begins clean.
