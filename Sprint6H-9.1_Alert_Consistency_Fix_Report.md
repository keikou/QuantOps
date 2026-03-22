# Sprint6H-9.1 Alert / Monitoring Consistency Fix Report

## Fixed issues

1. Overview `Open Alerts` now uses QuantOps alert service open-count semantics.
2. Dashboard overview now evaluates alert rules before returning counts.
3. Monitoring `/system` and `/execution` auto-refresh stale snapshots before returning payloads.
4. Topbar `System OK` pill now becomes dynamic:
   - `Critical Alerts N`
   - `Execution blocked/halted`
   - `System Degraded`
   - `System OK`
5. Execution state classification no longer leaves expired-plan situations stuck on `partially_filled` when there are no active plans but stale open/submitted child orders remain.
6. Added `stale_open_orders` reason for expired-plan + outstanding-order situations.

## Files changed

- `apps/quantops-api/app/services/alert_service.py`
- `apps/quantops-api/app/services/dashboard_service.py`
- `apps/quantops-api/app/schemas/dashboard.py`
- `apps/quantops-api/app/core/deps.py`
- `apps/quantops-api/app/services/monitoring_service.py`
- `apps/v12-api/ai_hedge_bot/execution/state_machine.py`
- `apps/quantops-frontend/src/components/layout/topbar.tsx`
- `apps/quantops-frontend/src/features/overview/overview-page.tsx`
- `apps/quantops-api/app/services/command_center_service.py`

## Validation

- Python compile check: passed
- Pytest collection against bundled environment: blocked by pre-existing migration SQL issue (`sqlite3.OperationalError: near "(": syntax error`) unrelated to this patch set.
