# Sprint5C patch overlay for Sprint4_V8_based_fixed

This overlay is designed for:
`Sprint4_real_impl/source_of_truth/quantops_sprint3/services/v12-api/`

## Adds
- risk engine modules
- governance modules
- sprint5c store/service
- API routes:
  - POST /runtime/run-sprint5c
  - GET /risk/latest
  - GET /risk/history
  - GET /analytics/performance
  - GET /analytics/alpha
  - GET /governance/budgets
  - GET /governance/regime
- migration SQL
- smoke test and PowerShell check script

## Manual merge points
- `ai_hedge_bot/app/main.py`
- `ai_hedge_bot/app/container.py`

Copy these files into the repo root of the v12-api service and run pytest for `tests/test_sprint5c_api.py`.
