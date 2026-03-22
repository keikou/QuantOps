# QuantOps Sprint6H-9.2.9

QuantOps is a local integrated trading operations workspace composed of three main applications:

- `apps/v12-api`: the V12 strategy and execution backend
- `apps/quantops-api`: the QuantOps control-plane and aggregation API
- `apps/quantops-frontend`: the Next.js operator GUI

The current version focuses on runtime observability plus recent-runs operational triage on top of the stabilized local stack: canonical runtime events/reasons, planner and execution-bridge diagnostics, command-center runtime aggregation, run-detail drilldown, runtime diagnostic bundles, recent-runs indexing, and reason/component-driven runtime triage views.

## Project Summary

This repository provides a local full-stack environment for:

- strategy runtime and execution data from V12
- aggregated control, monitoring, risk, portfolio, and command-center views from QuantOps API
- an operator-facing dashboard for Overview, Execution, Portfolio, Risk, Monitoring, Alerts, Scheduler, Strategies, Governance, Config, and Admin flows

The repo also contains `source_of_truth/` reference implementations and supporting tools used during the sprint history.

## Current Implementation

### Frontend

- Next.js App Router frontend in `apps/quantops-frontend`
- dashboard pages for:
  - Overview
  - Execution
  - Portfolio
  - Risk
  - Monitoring
  - Alerts
  - Scheduler
  - Strategies
  - Governance
  - Config
  - Admin
- API proxy layer under `src/app/api/proxy/[...path]/route.ts`
- typed API normalization and query hooks
- scoped status rendering for degraded, stale, and no-data states
- debug/status UI components for operator visibility
- runtime observability surfaces for:
  - timeline and block/degraded status
  - truth-based runtime badges and summary cards
  - run-detail drilldown at `/execution/runs/[runId]`
  - local runtime diagnostic bundle path visibility
  - recent runtime runs table with saved triage views and reason/component filters

### QuantOps API

- FastAPI service in `apps/quantops-api`
- route groups for:
  - dashboard
  - portfolio
  - risk
  - monitoring
  - execution
  - command center
  - alerts
  - scheduler
  - strategies
  - governance
  - approval
  - config
  - control
  - analytics
  - incidents
  - auth/admin/health/modes/acceptance
- stale-first fast paths for selected GUI endpoints
- request timing instrumentation for handler, serialization, and total request time
- debug/provenance endpoints for risk, monitoring, execution, overview, and portfolio validation
- live bridge logic from QuantOps to V12 for execution and overview truth
- command-center runtime aggregation for:
  - latest runtime truth
  - run-scoped debug/runtime drilldown
  - artifact bundle detection for local smoke outputs
  - recent-runs aggregation with state/reason/component/artifact filtering

### V12 API

- FastAPI service in `apps/v12-api`
- strategy, execution, portfolio, analytics, scheduler, market, runtime, and governance route surfaces
- startup paper loop support for local integrated runs
- upstream data source for QuantOps API aggregation
- runtime event/reason truth store and by-run diagnostics routes
- planner truth and execution-bridge diagnostics routes used by QuantOps run-detail pages

## TODO

- add runtime rollups / clustering summaries above Recent Runs
- add trend/incident-style summaries for top reason codes and blocking components
- continue operator UX cleanup around artifact presentation and evidence portability
- expand end-to-end validation for live GUI flows and slow first-load paths
- harden remaining write flows and permission gating
- add more build/test automation across the three-app stack
- review and reduce duplicated historical/reference content under `source_of_truth/`
- continue cleanup of legacy sprint-era docs and backup files where no longer needed

## CI And Regression Packs

- GitHub Actions frontend build workflow: `.github/workflows/frontend-build.yml`
- GitHub Actions QuantOps API regression workflow: `.github/workflows/quantops-api-regressions.yml`
- GitHub Actions runtime guard workflow: `.github/workflows/runtime-guard-checks.yml`
- GitHub Actions optional local-stack smoke workflow: `.github/workflows/optional-local-stack-smoke.yml`
- QuantOps API regression pack runner: `test_bundle/scripts/run_quantops_api_regression_pack.ps1`
- Regression pack documentation: `docs/ci_regression_packs.md`
- Developer startup/runbook: `docs/dev-startup.md`

## How To Run

### One-step local startup

From the repo root:

```bat
run_all.cmd
```

This opens three windows:

- V12 API: `http://localhost:8000`
- QuantOps API: `http://localhost:8010`
- QuantOps Frontend: `http://localhost:3000`

### Individual startup

```bat
start_v12_api.cmd
start_quantops_api.cmd
start_frontend.cmd
```

### Local startup smoke

```powershell
powershell -ExecutionPolicy Bypass -File test_bundle/scripts/run_local_startup_smoke.ps1
```

This smoke script starts the three local services, checks core health routes, verifies the frontend home page and QuantOps overview endpoint, and then shuts the started processes down so the next run begins clean.

It also runs a paper cycle, validates runtime observability truth for the returned `run_id`, and writes a timestamped diagnostic bundle under `test_bundle/artifacts/runtime_diagnostics/`.

### Startup behavior

- `start_v12_api.cmd` creates `apps/v12-api/.venv` if needed, installs requirements once, and starts Uvicorn on port `8000`
- `start_quantops_api.cmd` creates `apps/quantops-api/.venv` if needed, installs requirements once, runs DB migration, and starts Uvicorn on port `8010`
- `start_frontend.cmd` installs frontend dependencies if `node_modules` is missing, then starts Next.js on port `3000`

### Developer runbook

See `docs/dev-startup.md` for:

- startup order
- ports and health routes
- `127.0.0.1` local routing expectations
- heavy-route timeout budgets
- smoke-check commands

## Useful URLs

- Frontend: [http://localhost:3000](http://localhost:3000)
- V12 API: [http://localhost:8000](http://localhost:8000)
- QuantOps API: [http://localhost:8010](http://localhost:8010)

## Repository Notes

- See `safe_for_clean.md` for generated/runtime artifacts that are safe to delete before packaging or publishing
- Local `.env` files, virtual environments, caches, runtime databases, and runtime snapshots are intentionally excluded from Git
