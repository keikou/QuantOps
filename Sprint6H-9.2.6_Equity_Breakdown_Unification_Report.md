# Sprint6H-9.2.6 Equity Breakdown Unification

## Goal
Unify `Total Equity` across Overview and Portfolio using one calculation model:

- `Used Margin = Σ(abs(Qty) * Avg)`
- `Unrealized = Σ(PnL)`
- `Free Margin = Balance + Unrealized - Used Margin`
- `Total Equity = Used Margin + Free Margin = Balance + Unrealized`

## Main changes
- Added shared backend calculator: `apps/quantops-api/app/services/equity_breakdown.py`
- Portfolio API now returns:
  - `balance`
  - `used_margin`
  - `free_margin`
  - `unrealized`
  - `total_equity`
- Dashboard overview now uses the same equity calculator, so Overview and Portfolio read the same total equity source.
- Frontend Overview and Portfolio pages now display the same breakdown fields.
- Added `asOf` / `lastUpdated` visibility alongside the equity formula note.

## Files changed
- `apps/quantops-api/app/services/equity_breakdown.py` (new)
- `apps/quantops-api/app/services/portfolio_service.py`
- `apps/quantops-api/app/services/dashboard_service.py`
- `apps/quantops-api/app/schemas/portfolio.py`
- `apps/quantops-frontend/src/types/api.ts`
- `apps/quantops-frontend/src/lib/api/normalize.ts`
- `apps/quantops-frontend/src/lib/api/hooks.ts`
- `apps/quantops-frontend/src/features/overview/overview-page.tsx`
- `apps/quantops-frontend/src/features/portfolio/page.tsx`

## Validation
- Python compile check passed for `apps/quantops-api/app`

## Notes
- This unifies display-time equity values. Position-close balance mutation logic remains downstream in the trading/runtime layer and is not rewritten here.
