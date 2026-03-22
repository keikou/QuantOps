# Sprint6H-9.2.6.1 Equity Breakdown Bugfix Report

## Fixed
- corrected `equity_breakdown.py` field extraction bug that caused `dict.get()` to receive 3 arguments
- added `_first_of(...)` helper for safe multi-key lookup
- hardened dashboard and portfolio services so equity breakdown errors no longer crash the whole endpoint
- preserved fallback `total_equity` from summary payload when breakdown computation fails

## Files changed
- `apps/quantops-api/app/services/equity_breakdown.py`
- `apps/quantops-api/app/services/dashboard_service.py`
- `apps/quantops-api/app/services/portfolio_service.py`
- `apps/quantops-api/app/tests/test_sprint6h9_2_6_equity_breakdown_fix.py`

## Added tests
- multiple position field aliases: `avg_price`, `avg_entry_price`, `avg`
- `None` / missing values are tolerated
- dashboard overview survives equity breakdown failure
- portfolio overview survives equity breakdown failure

## Verification
Executed:

```bash
cd apps/quantops-api
pytest -q app/tests/test_sprint6h9_2_6_equity_breakdown_fix.py
```

Result:
- `6 passed`
