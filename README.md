# QuantOps V12

QuantOps is a local integrated trading operations workspace composed of three main applications:

- `apps/v12-api`: the V12 strategy and execution backend
- `apps/quantops-api`: the QuantOps control-plane and aggregation API
- `apps/quantops-frontend`: the Next.js operator GUI

The current `main` branch reflects the post-SprintH and post-closure state:

- broad timeout mitigation is complete
- `Phase1 Truth Layer` is complete
- `Phase2 Execution Reality` is complete
- `Phase3 Portfolio Intelligence` is complete
- main GUI paths are stabilized on summary/read-model style routes
- QuantOps summary contracts explicitly distinguish stable and display semantics
- writer observability and incremental writer behavior are in place
- startup and stop scripts are verified and documented
- SprintH closeout docs and AI/developer onboarding docs are now part of the repo

## Project Summary

This repository provides a local full-stack environment for:

- strategy runtime and execution data from V12
- aggregated control, monitoring, risk, portfolio, and command-center views from QuantOps API
- an operator-facing dashboard for Overview, Execution, Portfolio, Risk, Monitoring, Alerts, Scheduler, Strategies, Governance, Config, and Admin flows

The repo also contains `source_of_truth/` reference implementations and supporting tools used during the sprint history.

## Start Here

If you are new to this repo, read these first:

1. `docs/Development for AI.md`
2. `docs/After_Sprint6H_Roadmap_from_Architect.md`
3. `docs/SprintH_completion_report.md`
4. `docs/Sprint6H_truth_completion_final.md`
5. `docs/Phase2_execution_completion_final.md`
6. `docs/Phase3_allocation_completion_final.md`
7. `docs/correlation-logging-guide.md`
8. `docs/development-rules-v12-vs-quantops.md`
9. `docs/development-workflow.md`
10. `docs/ops-runbook.md`
11. `docs/dev-startup.md`
12. `docs/ci_regression_packs.md`

These documents capture the current architecture direction, development rules, startup path, regression surface, and SprintH closeout status.
`docs/correlation-logging-guide.md` is the shortest practical path for tracing a page access, API timeout, or backend failure across frontend, QuantOps API, and V12 by `trace_id`.

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
  - structured run-stage timeline with stage state, evidence, and root-cause clues
  - run forensics summary for status, trigger, mode, and duration
  - local runtime diagnostic bundle path visibility
  - recent runtime runs table with diagnosis-backed saved views and reason/component filters
  - active runtime issue rollups with diagnosis severity, retryability, recurrence, and trend
  - run-detail diagnosis card with recurrence context and remediation hints

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
  - structured stage normalization across cycle start, planner, bridge, submission, fill, portfolio update, artifacts, and completion
  - V12 run-record linkage for status, trigger, duration, checkpoints, and audit logs
  - artifact bundle detection for local smoke outputs
  - recent-runs aggregation with state/reason/component/artifact filtering

### V12 API

- FastAPI service in `apps/v12-api`
- strategy, execution, portfolio, analytics, scheduler, market, runtime, and governance route surfaces
- startup paper loop support for local integrated runs
- upstream data source for QuantOps API aggregation
- runtime event/reason truth store and by-run diagnostics routes
- planner truth and execution-bridge diagnostics routes used by QuantOps run-detail pages

## Current Status

SprintH is complete.

Phase closure status is:

- `Phase1 Truth Layer = COMPLETE`
- `Phase2 Execution Reality = COMPLETE`
- `Phase3 Portfolio Intelligence = COMPLETE`

The next roadmap target is no longer SprintH closeout or Phase2/3 closure. The next roadmap target is Phase4+ work such as Alpha Factory, Risk / Guard OS, and later live-trading readiness.

See:

- `docs/SprintH_completion_report.md`
- `docs/sprinth-finish-plan.md`
- `docs/Sprint6H_truth_completion_final.md`
- `docs/Phase2_execution_completion_final.md`
- `docs/Phase3_allocation_completion_final.md`
- `docs/After_Sprint6H_Roadmap_from_Architect.md`

## CI And Regression Packs

- GitHub Actions frontend build workflow: `.github/workflows/frontend-build.yml`
- GitHub Actions QuantOps API regression workflow: `.github/workflows/quantops-api-regressions.yml`
- GitHub Actions runtime guard workflow: `.github/workflows/runtime-guard-checks.yml`
- GitHub Actions optional local-stack smoke workflow: `.github/workflows/optional-local-stack-smoke.yml`
- QuantOps API regression pack runner: `test_bundle/scripts/run_quantops_api_regression_pack.ps1`
- Regression pack documentation: `docs/ci_regression_packs.md`
- Developer startup notes: `docs/dev-startup.md`
- Operations runbook: `docs/ops-runbook.md`

## How To Run

### One-step local startup

From the repo root:

```bat
run_all.cmd
```

This opens three windows:

- V12 API: `http://127.0.0.1:8000`
- QuantOps API: `http://127.0.0.1:8010`
- QuantOps Frontend: `http://127.0.0.1:3000`

### Individual startup

```bat
start_v12_api.cmd
start_quantops_api.cmd
start_frontend.cmd
start_frontend_prod_fast.cmd
```

`start_frontend_prod_fast.cmd` is the one-click frontend fast path when you already have a valid production build under `apps/quantops-frontend/.next`.

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
- `start_frontend_prod_fast.cmd` starts the frontend production server without running a build step, so it should be used only when the existing `.next` output is already present and trusted

### Developer runbook

See `docs/dev-startup.md` for:

- startup order
- ports and health routes
- `127.0.0.1` local routing expectations
- heavy-route timeout budgets
- smoke-check commands

See `docs/ops-runbook.md` for:

- start/stop operations
- log locations
- correlation logging and timeout analysis entry points
- writer closeout checks
- common local failure modes
- verified local behavior

See `docs/correlation-logging-guide.md` for:

- where `frontend_events.jsonl`, `quantops_requests.jsonl`, `quantops_upstream_v12.jsonl`, and `v12_requests.jsonl` fit together
- how to investigate slow page loads, frontend timeouts, and V12 upstream timeouts using `trace_id`
- how to use `test_bundle/scripts/analyze_correlation_timeouts.py`

## Useful URLs

- Frontend: [http://127.0.0.1:3000](http://127.0.0.1:3000)
- V12 API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- QuantOps API: [http://127.0.0.1:8010](http://127.0.0.1:8010)

## Repository Notes

- See `safe_for_clean.md` for generated/runtime artifacts that are safe to delete before packaging or publishing
- Local `.env` files, virtual environments, caches, runtime databases, and runtime snapshots are intentionally excluded from Git
- For AI handoff and rapid continuation, start with `docs/Development for AI.md`
- For timeout and incident tracing, follow `docs/correlation-logging-guide.md`
