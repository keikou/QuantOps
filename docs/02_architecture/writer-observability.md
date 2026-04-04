# Writer Observability

This document explains the writer-side observability added during timeout improvement.

## Why Writer Observability Exists

The early timeout analysis showed that read-path tuning alone was not enough.

The backend needed a way to answer:

- Is the writer doing full rebuilds?
- Are fills being scanned incrementally or fully?
- Is position write cost dominating the cycle?
- Is equity work still falling back to a heavy path?

Writer observability was added to make those answers visible.

## Main Log Files

- `runtime/logs/writer_cycles.jsonl`
- `runtime/logs/orchestrator_runs.jsonl`

These files are local operational diagnostics for V12 runtime behavior.

## Main Metrics

The exact shape can evolve, but recent fields include metrics like:

- `cycle_duration_ms`
- `record_orders_and_fills_ms`
- `rebuild_positions_ms`
- `compute_equity_snapshot_ms`
- `fills_scanned_positions`
- `fills_scanned_equity`
- `new_fills_applied`
- `rebuild_mode`
- `position_row_write_duration_ms`
- `position_history_rows_written`
- `position_snapshot_version`
- `equity_full_rebuild_reason`
- `full_rebuild_reason`
- `position_rollup_source`

## How To Read Them

### `rebuild_mode`

Typical meaning:

- `full`
  - expensive path
- `incremental`
  - normal desired path

### `fills_scanned_positions` / `fills_scanned_equity`

Healthy trend:

- no-fill cycles near `0`
- fill cycles only scan delta fills, not historical full sets

### `position_row_write_duration_ms`

This is the easiest way to see whether position writes are still too expensive.

After the recent changes:

- no-fill cycles should often be near `0`
- fill cycles should be bounded by affected rows, not full snapshot rewrites

### `position_history_rows_written`

Healthy trend:

- `0` on no-fill cycles
- small values on fill cycles, ideally matching affected rows

### `full_rebuild_reason` / `equity_full_rebuild_reason`

These are the most important fallback diagnostics.

Examples of reasons:

- missing active snapshot
- missing previous snapshot
- missing fill watermark

Healthy trend:

- `null` or absent during normal operation

## What Good Looks Like

Good recent behavior looks like:

- no-fill cycle:
  - `fills_scanned_* = 0`
  - `position_row_write_duration_ms = 0`
  - very small `rebuild_positions_ms`
- fill cycle:
  - small `new_fills_applied`
  - small `position_history_rows_written`
  - no full rebuild reason

## What Bad Looks Like

Investigate when you see:

- frequent `full` rebuild mode
- repeated non-null full rebuild reasons
- large fill scan counts in routine cycles
- row write duration dominating the cycle
- cycle duration jumping without corresponding new fill volume

## Suggested Troubleshooting Order

1. Check `full_rebuild_reason`
2. Check `fills_scanned_positions` and `fills_scanned_equity`
3. Check `position_row_write_duration_ms`
4. Check `position_history_rows_written`
5. Compare no-fill cycles vs fill cycles

This usually tells you whether the bottleneck is:

- missing state/watermark
- too much fill scanning
- too much row rewrite
- or equity fallback behavior

## Current State

After the timeout-improvement work:

- no-fill cycles avoid unnecessary position snapshot rewrites
- fill cycles update affected rows instead of rewriting the whole snapshot history
- equity reuses same-cycle fill fetch and position rollups

This means writer observability is now less about discovering catastrophic rebuilds and more about catching regressions.

## Related Docs

- [timeout-roadmap.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/06_playbooks/timeout-roadmap.md)
- [architecture-read-models.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/02_architecture/architecture-read-models.md)
