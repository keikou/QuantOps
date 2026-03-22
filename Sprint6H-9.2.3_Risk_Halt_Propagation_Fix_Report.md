# Sprint6H-9.2.3 Risk Halt Propagation Fix Report

## Summary
Sprint6H-9.2.3 implements the full set of requested fixes around:
- risk halt / kill switch propagation into planner and execution truth
- residual open order handling after halt
- execution reason freshness and priority cleanup
- topbar / overview safety-state reflection
- overview vs risk net exposure consistency
- stale order and order accumulation alerts

## Key Backend Changes

### V12 API
- `apps/v12-api/ai_hedge_bot/execution/state_machine.py`
  - Added reason/state handling for:
    - `kill_switch_triggered`
    - `blocked_by_risk`
    - `residual_orders_after_halt`
    - `open_orders_not_draining`
    - `working_orders`
    - `recent_execution_activity`
    - `stale_open_orders`
  - Shortened recent activity TTL semantics.
  - Prevented `expired_plan` from dominating live execution reasons.
  - Halt + residual orders now resolves to degraded/halted truth instead of looking healthy.

- `apps/v12-api/ai_hedge_bot/api/routes/execution.py`
  - Planner activity enrichment now accepts `trading_state`.
  - Halted/paused states force planner items into blocked/halted residual activity states instead of `executing`.
  - Execution state endpoint keeps residual order counts visible after halt.
  - Reason selection now uses explicit priority ordering so safety/risk reasons beat stale historical reasons.
  - `recent_execution_activity` is no longer sticky in halted scenarios.

### QuantOps API
- `apps/quantops-api/app/services/monitoring_service.py`
  - Worker state is now computed from a composite of:
    - runtime timestamps
    - execution state freshness
    - planner activity freshness
    - fill freshness
    - active/open/submitted order truth
  - Added risk truth fields to monitoring payload:
    - `riskTradingState`
    - `killSwitch`
    - `alertState`
  - Hardened datetime freshness parsing by routing through the same tz-aware parser.

- `apps/quantops-api/app/services/dashboard_service.py`
  - Overview net/gross exposure now prefers portfolio dashboard summary values to align sign convention with risk page.

- `apps/quantops-api/app/services/command_center_service.py`
  - Overview now exposes execution/risk truth fields needed by the frontend.

- `apps/quantops-api/app/services/alert_service.py`
  - Added `stale_open_orders` alert creation.
  - Added `execution_order_accumulation` critical alert for blocked/halted/stale scenarios with large residual order counts.
  - Execution degraded alerts now include reason context.

## Frontend Changes
- `apps/quantops-frontend/src/components/layout/topbar.tsx`
  - Topbar now checks risk halt / kill switch directly.
  - `System OK` is no longer shown when risk is halted or kill switch is triggered.

- `apps/quantops-frontend/src/features/overview/overview-page.tsx`
  - Live Snapshot now shows:
    - risk trading state
    - kill switch state

- `apps/quantops-frontend/src/lib/api/normalize.ts`
- `apps/quantops-frontend/src/types/api.ts`
  - Added frontend handling for the new monitoring risk truth fields.

## Tests Added
- `apps/quantops-api/app/tests/test_sprint6h9_2_3_risk_truth.py`
- `apps/v12-api/tests/test_sprint6h9_2_3_risk_halt_propagation.py`

## Validation
### QuantOps API
- `pytest -q app/tests/test_sprint6h9_monitoring_truth.py app/tests/test_sprint6h9_2_3_risk_truth.py`
- Result: `2 passed`

### V12 API
- `pytest -q tests/test_sprint6h9_execution_observability.py tests/test_sprint6h9_2_3_risk_halt_propagation.py`
- Result: `3 passed`

## Outcome
This Sprint6H-9.2.3 package addresses the remaining gaps observed across screenshots:
- halted risk state now propagates more clearly into execution truth
- residual orders after halt remain visible instead of being silently zeroed out
- stale/recent execution reasons are no longer misleadingly sticky
- top-level health reflects trading safety, not just process liveness
- stale/open order accumulation is now surfaced with stronger alerts
