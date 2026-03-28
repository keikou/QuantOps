# Portfolio Display Semantics

This document explains how normal QuantOps Portfolio display differs from lower-level V12 truth rows.

## Why This Exists

V12 truth tracks positions at a finer grain:

- `symbol`
- `strategy_id`
- `alpha_family`

That is correct for accounting and observability, but it is too noisy for the normal Portfolio page when multiple legs exist for the same symbol.

The normal Portfolio page therefore uses a user-facing aggregated display.

## Truth Rows vs Display Rows

### Truth rows

Source concept:

- multiple rows for the same symbol can exist
- each row can have a different `strategy_id`
- each row can have its own `avg_entry_price`, `signed_qty`, and PnL

### Display rows

Normal Portfolio display:

- aggregates the same symbol into a single row
- keeps the V12 truth intact underneath
- is meant for operator readability, not raw truth inspection

## Quantity Semantics

The normal display uses signed quantity logic.

- long quantity is positive
- short quantity is negative

Aggregation:

- `long + long` adds
- `short + short` adds
- `long + short` offsets

This means the displayed quantity is the net quantity for the symbol.

## Average Price Semantics

For the normal aggregated display, average price is computed from the aggregated signed quantity inputs used for the display row.

This is intended as a user-facing net display value, not a replacement for lower-level truth accounting.

The truth/accounting logic still lives in V12.

## Margin Semantics

Used Margin and Free Margin on the Portfolio page should be based on the aggregated display positions, not raw duplicate symbol rows.

Why:

- raw duplicate rows can overstate apparent used margin in the user-facing page
- the normal Portfolio page should align with the net symbol view shown to the user

This was updated so the Portfolio page and position table use the same aggregation basis.
The V12 `equity_snapshots.used_margin` truth is now also computed on the same symbol-aggregated signed entry basis, and exposure ratios in the equity snapshot use the same symbol-aggregated market value basis, while the lower-level position truth rows remain unchanged.

## Strategy vs Alpha Family

### Why `Strategy` was removed from the normal display

The raw `strategy_id` could appear as values like:

- `run_20260325062302_e976b013`

That is not a human-friendly strategy name. It is closer to an execution/run identifier or fallback source identifier.

For normal UI, that is too technical and often misleading.

### Current normal display

Normal Portfolio display now shows:

- `Primary Alpha Family`

instead of raw `Strategy`.

Examples:

- `Trend`
- `Mean Reversion`
- `Runtime`

This is more stable and more understandable for user-facing display.

## What Is Still Available Internally

The lower-level truth still preserves:

- `strategy_id`
- `alpha_family`
- per-row signed quantity
- per-row average entry
- per-row realized/unrealized PnL

So:

- display is simplified
- truth is not lost

## Intended Use

Use the normal Portfolio page for:

- net symbol exposure
- user-facing portfolio reading
- operator-friendly margin/exposure understanding

Use debug/truth views for:

- per-strategy inspection
- provenance
- lower-level accounting investigation

## Related Docs

- [api-summary-contracts.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/api-summary-contracts.md)
- [architecture-read-models.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/architecture-read-models.md)
