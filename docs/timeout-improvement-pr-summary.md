# Timeout Improvement PR Summary

## Scope

This branch focuses on reducing timeout waves across:

- Overview
- Portfolio
- Execution
- Runtime / Command Center
- Risk / Monitoring / Alerts startup paths

The work spans:

- V12 writer cost reduction
- V12 summary/read-model route additions
- QuantOps stale-first/cache/coalescing
- frontend stable/live presentation cleanup
- startup sequencing and warmup throttling

## What Changed

### 1. V12 writer became meaningfully more incremental

Key changes:

- versioned `position_snapshots_latest` instead of delete/rebuild
- fill watermark tracking for positions and equity
- no-fill cycles avoid position snapshot rewrites
- fill cycles update affected rows instead of rewriting all rows
- equity snapshots reuse:
  - position realized pnl
  - same-cycle fill fetch
  - same-cycle position rollups

Main files:

- [apps/v12-api/ai_hedge_bot/services/truth_engine.py](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/v12-api/ai_hedge_bot/services/truth_engine.py)
- [apps/v12-api/ai_hedge_bot/orchestrator/orchestration_service.py](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/v12-api/ai_hedge_bot/orchestrator/orchestration_service.py)

### 2. Read paths moved closer to stable read models

Added or promoted summary routes:

- V12 `/portfolio/overview-summary/latest`
- V12 `/portfolio/metrics/latest`
- V12 `/execution/view/latest`
- cached V12 summary routes for portfolio/runtime/risk/quality

QuantOps major paths now prefer summary/read-model style upstreams and use stale-first/cached responses where appropriate.

Main files:

- [apps/v12-api/ai_hedge_bot/api/routes/portfolio.py](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/v12-api/ai_hedge_bot/api/routes/portfolio.py)
- [apps/v12-api/ai_hedge_bot/api/routes/execution.py](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/v12-api/ai_hedge_bot/api/routes/execution.py)
- [apps/v12-api/ai_hedge_bot/api/routes/runtime.py](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/v12-api/ai_hedge_bot/api/routes/runtime.py)
- [apps/quantops-api/app/services/dashboard_service.py](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/app/services/dashboard_service.py)
- [apps/quantops-api/app/services/portfolio_service.py](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/app/services/portfolio_service.py)
- [apps/quantops-api/app/services/execution_service.py](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/app/services/execution_service.py)
- [apps/quantops-api/app/services/command_center_service.py](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/app/services/command_center_service.py)

### 3. Stable/live contracts became explicit

Major summary responses now expose explicit mixed-value contracts:

- `stable_value`
- `live_delta`
- `display_value`

This was added to:

- execution summary
- runtime summary
- overview summary
- portfolio overview
- portfolio metrics

Frontend now consumes those contracts in the major pages.

Main files:

- [apps/quantops-frontend/src/types/api.ts](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-frontend/src/types/api.ts)
- [apps/quantops-frontend/src/lib/api/normalize.ts](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-frontend/src/lib/api/normalize.ts)
- [apps/quantops-frontend/src/features/overview/overview-page.tsx](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-frontend/src/features/overview/overview-page.tsx)
- [apps/quantops-frontend/src/features/portfolio/page.tsx](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-frontend/src/features/portfolio/page.tsx)
- [apps/quantops-frontend/src/features/execution/page.tsx](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-frontend/src/features/execution/page.tsx)

### 4. Startup and burst behavior were thinned

Improvements include:

- V12 health/readiness wait before GUI warmup
- delayed and summary-only risk/monitoring warmup
- reduced page prefetch burst
- staged Overview secondary reads
- short TTL cache + coalescing for repeated live-feed style reads
- retry/backoff for transient startup proxy reads

Main files:

- [apps/quantops-api/app/main.py](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/app/main.py)
- [apps/quantops-frontend/src/components/layout/sidebar.tsx](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-frontend/src/components/layout/sidebar.tsx)
- [apps/quantops-frontend/src/features/overview/overview-page.tsx](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-frontend/src/features/overview/overview-page.tsx)
- [test_bundle/scripts/start_local_stack.ps1](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/test_bundle/scripts/start_local_stack.ps1)
- [test_bundle/scripts/start_local_stack_prod.ps1](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/test_bundle/scripts/start_local_stack_prod.ps1)

### 5. Portfolio display semantics were cleaned up

Changes:

- duplicate symbol rows are aggregated for normal Portfolio display
- margin uses aggregated positions instead of raw duplicate rows
- `Strategy` display was removed in favor of `Primary Alpha Family`

Main files:

- [apps/quantops-api/app/services/portfolio_service.py](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-api/app/services/portfolio_service.py)
- [apps/quantops-frontend/src/features/portfolio/page.tsx](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/apps/quantops-frontend/src/features/portfolio/page.tsx)

## Observed Outcome

Recent real-stack verification showed:

- no reproduced GUI timeout across the main pages
- first-hit live builds usually land in the `300-450ms` range
- repeated reads usually land in the `1-12ms` range

Representative examples:

- `/api/v1/dashboard/overview`: about `991ms -> 1-2ms`
- `/api/v1/portfolio/overview`: about `321ms -> <3ms`
- `/api/v1/portfolio/positions`: about `443ms -> <3ms`
- `/api/v1/portfolio/metrics`: about `339ms -> 1-12ms`
- `/api/v1/execution/planner/latest` + `/state/latest` replaced by `/view/latest`
- `/api/v1/command-center/runtime/latest`: about `297ms -> <2ms`

## Remaining Work

This branch leaves only refinement work, not broad timeout mitigation:

- optional further profiling of the equity path
- optional expansion of freshness metadata such as:
  - `source_fill_watermark`
  - `rebuilt_at`
- final review of whether any remaining mixed secondary summaries should expose explicit stable/display contracts

## Validation

Validation used across this branch included:

- targeted `pytest` for V12 and QuantOps services/routes
- frontend `npm run build`
- repeated real-stack runs through:
  - `/`
  - `/portfolio`
  - `/execution`
  - `/risk`
  - `/monitoring`
  - `/alerts`
  - `/scheduler`

## Suggested PR Framing

Suggested top-level PR framing:

1. Reduce writer contention and remove the worst rebuild patterns
2. Move major GUI reads onto cached summary/read-model paths
3. Make stable/live response contracts explicit in backend and frontend
4. Thin startup/warmup burst behavior
