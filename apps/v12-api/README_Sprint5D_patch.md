# Sprint5D patch overlay for Sprint4_V8_based_fixed

This overlay is designed for:

`Sprint4_real_impl/source_of_truth/quantops_sprint3/services/v12-api/`

## Adds
- runtime mode core
- mode rules
- Sprint5D store / service
- API routes:
  - POST `/runtime/run-with-mode`
  - GET `/runtime/modes`
  - GET `/runtime/modes/current`
  - POST `/runtime/modes/set`
  - GET `/runtime/modes/runs/latest`
  - GET `/acceptance/status`
  - GET `/acceptance/checks`
  - POST `/acceptance/run`
  - GET `/incidents/latest`
  - GET `/incidents/history`
  - GET `/analytics/shadow-summary`
- migration SQL
- smoke tests and PowerShell check script

## Manual merge points
- `ai_hedge_bot/app/main.py`
- `ai_hedge_bot/app/container.py`

## Notes
- `live_ready` is intentionally dry-run only and always blocks external send.
- shadow mode stores `shadow_pnl_snapshots`.
- critical validation failures create incident records.
