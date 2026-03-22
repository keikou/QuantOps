# Sprint6H-9.2.7.1 QtySign Truth Correction

## Summary
This correction updates the truth-layer accounting model to use **qty sign as the source of truth** for calculations while keeping **signed_fill / abs(qty)** for UI display only.

## Corrected accounting model
- buy / long: `qty > 0`
- sell / short: `qty < 0`
- UI display fill size: `abs(qty)`

### Cash
- `delta_cash = -(qty * fill_price) - fee`
- `cash_balance = initial_capital + Σ delta_cash`

### Market value
- `market_value = Σ(qty * mark_price)`

### Equity
- `total_equity = cash_balance + market_value`

### Margin
- `used_margin = Σ(abs_qty * avg_entry_price)`
- `available_margin = max(total_equity - used_margin, 0)`

### QuantOps breakdown
- prefer `total_equity` from V12 summary
- `free_margin = total_equity - used_margin`

## Files changed
- `apps/v12-api/ai_hedge_bot/services/truth_engine.py`
- `apps/quantops-api/app/services/equity_breakdown.py`
- `apps/v12-api/tests/test_sprint6h9_2_7_1_qty_sign_truth_correction.py`
- `apps/quantops-api/app/tests/test_sprint6h9_2_7_1_qty_sign_truth_breakdown.py`

## Implementation notes
- Added `_fill_signed_qty(...)` helper to normalize signed qty from existing fill payloads.
- Kept backward compatibility with current fill payloads where `fill_qty` may still be positive and `side` determines sign.
- `record_orders_and_fills(...)` now stores UI order qty as absolute size but computes cash using signed qty truth.
- `_compute_cash_balance_from_fills(...)` and `_build_position_states_from_fills(...)` now use the same signed qty truth helper.
- `equity_breakdown.py` now recognizes `signed_qty` when deriving used margin from positions.

## Validation
### V12 API tests
- `tests/test_sprint6h9_2_7_signed_qty_equity_truth.py`
- `tests/test_sprint6h9_2_7_1_qty_sign_truth_correction.py`
- result: **4 passed**

### QuantOps API tests
- `app/tests/test_sprint6h9_2_7_equity_breakdown_truth.py`
- `app/tests/test_sprint6h9_2_7_1_qty_sign_truth_breakdown.py`
- result: **2 passed**
