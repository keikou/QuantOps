# Sprint6H-9.2.7 SignedQty Equity Truth Fix

## Summary
Implemented signed-qty equity truth fixes across V12 truth-engine and QuantOps equity breakdown.

## Main changes
- Unified cash accounting to signed-qty form:
  - `signed_fill = +qty` for buy, `-qty` for sell
  - `delta_cash = -(signed_fill * fill_price) - fee`
- Added replay-based cash balance computation from execution fills
  - avoids stale / missing ledger dependence during equity snapshot generation
- Fixed equity snapshot truth:
  - `cash_balance = initial_capital + Σ delta_cash`
  - `market_value = Σ(signed_qty * mark_price)`
  - `total_equity = cash_balance + market_value`
- Margin-style fields now derive from total equity truth:
  - `used_margin = Σ(abs_qty * avg_entry_price)`
  - `available_margin = max(total_equity - used_margin, 0)`
- QuantOps equity breakdown now prefers upstream truth values
  - `total_equity` from V12 summary is preserved
  - `free_margin = total_equity - used_margin`

## Files changed
- `apps/v12-api/ai_hedge_bot/services/truth_engine.py`
- `apps/quantops-api/app/services/equity_breakdown.py`
- `apps/quantops-api/app/services/dashboard_service.py`
- `apps/quantops-api/app/services/portfolio_service.py`
- `apps/v12-api/tests/test_sprint6h9_2_7_signed_qty_equity_truth.py`
- `apps/quantops-api/app/tests/test_sprint6h9_2_7_equity_breakdown_truth.py`

## Validation
- `apps/v12-api`: `2 passed`
- `apps/quantops-api`: `1 passed`

## Notes
This change makes `Total Equity` follow signed-qty truth even with many shorts:
- long: positive `signed_qty`
- short: negative `signed_qty`
- no separate buy/sell cash formulas needed beyond signed-qty conversion
