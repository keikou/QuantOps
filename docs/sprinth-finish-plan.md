# SprintH Finish Plan

This document turns the current `main` state into a practical finish plan for SprintH.

It is based on the current code, docs, scripts, and regression surface already merged into `main`.

## Current State

The broad timeout-improvement phase is effectively complete.

Recent merged work already established:

- stale-first behavior on key QuantOps reads
- short TTL cache on major summary paths
- in-flight coalescing on repeated reads
- startup sequencing and warmup throttling
- explicit stable/live/display contracts on the main GUI summary surfaces
- writer observability
- versioned position snapshots
- fill watermark-based incremental writer behavior
- reduced no-fill rewrite cost
- affected-row-only position updates
- improved runtime and execution summary paths
- startup and stop script hardening

The current branch state is operationally in refinement mode, not emergency timeout mitigation mode.

## What Is Confirmed Complete

### Main GUI path direction

The main GUI paths are already aligned to the intended architecture:

- V12 remains correctness-first
- QuantOps API remains contract-and-latency-first
- frontend separates stable summary from live feed
- read-model and summary routes are preferred over heavy truth reads

### Main summary contracts

The major summary surfaces already carry explicit or equivalent operator-facing metadata:

- `stable_value`
- `live_delta`
- `display_value`
- `build_status`
- `source_snapshot_time`
- `rebuilt_at`
- `data_freshness_sec`

This is already established on the primary Overview, Portfolio, Execution, and runtime summary surfaces.

### Startup and local operations

The local run and stop scripts are in place and documented:

- `run_all.cmd`
- `run_all_prod.cmd`
- `run_all_prod_fast.cmd`
- `start_v12_api.cmd`
- `start_quantops_api.cmd`
- `start_frontend.cmd`
- `start_frontend_prod.cmd`
- `stop_all.cmd`
- `stop_all_prod.cmd`
- `stop_v12_api.cmd`
- `stop_quantops_api.cmd`
- `stop_frontend.cmd`
- `test_bundle/scripts/stop_ports.ps1`

### Regression direction

The current regression packs already protect the major timeout-improvement direction:

- truth binding
- stale-first behavior
- debug/provenance surfaces
- startup hardening
- frontend timeout policy
- V12 runtime observability

## What Is Not Fully Closed Yet

These are the remaining finish items that still need an explicit decision or final verification.

### 1. Equity writer final profiling

The equity path has already been made more incremental, but the remaining work is to prove the path is actually closed out in practice.

What is already true:

- position writer uses fill watermark state
- no-fill cycles avoid unnecessary snapshot rewrites
- fill cycles update affected rows
- equity path reuses same-cycle fill fetch
- equity path reuses same-cycle position rollups

What still needs to be closed:

- confirm whether routine cycles still hit unexpected full fallback behavior
- confirm restart behavior does not cause repeated watermark-related rebuilds
- confirm no hidden aggregate remains material in `compute_equity_snapshot()`

Current log read from local artifacts:

- observed fill cycles show bounded writer sub-costs
- observed `position_row_write_duration_ms` is generally small
- observed `compute_equity_snapshot_ms` is materially lower than earlier broad timeout phases
- observed full rebuild reasons still appear on bootstrap-like runs as:
  - `missing_active_snapshot`
  - `missing_previous_snapshot`

This suggests the main remaining question is not broad cycle cost, but whether restart/bootstrap fallback behavior is acceptable and non-recurring after the first stabilized cycle.

Additional real-stack check on 2026-03-28:

- repeated no-fill cycles showed:
  - `fills_scanned_positions = 0`
  - `fills_scanned_equity = 0`
  - `position_row_write_duration_ms = 0`
  - `position_history_rows_written = 0`
  - no rebuild reason
- a restart-followed paper cycle showed:
  - non-zero fill delta
  - no `position_full_rebuild_reason`
  - no `equity_full_rebuild_reason`

This materially reduces the remaining SprintH uncertainty around writer restart convergence.

### 2. Secondary route contract cleanup

The primary GUI routes are already in good shape.

The remaining question is whether any secondary summary responses should also adopt the full stable/live/display contract style.

Current working view:

- likely yes:
  - `analytics/equity-history`
- likely no:
  - `risk` summary surfaces
  - `monitoring` summary surfaces
- keep as-is:
  - debug and provenance routes

The criterion is not “make everything uniform”.
The criterion is whether the response is a mixed operator-facing summary that benefits from explicit stable/display semantics.

### 3. Optional freshness contract expansion

`source_fill_watermark` is still documented as a possible future field, but it is not broadly exposed in current response contracts.

This should remain optional unless profiling or operator workflow shows that it materially improves diagnosis.

## SprintH Work Packages

### Work Package A: V12 writer closeout

Goal:
Prove the writer/equity path is operationally stable under normal local runtime conditions.

Tasks:

- inspect `runtime/logs/writer_cycles.jsonl`
- inspect `runtime/logs/orchestrator_runs.jsonl`
- compare no-fill cycles versus fill cycles
- confirm `full_rebuild_reason` is usually null or absent in normal operation
- confirm `missing_fill_watermark` is not recurring after warm startup
- confirm `history_rows_written` stays near zero on no-fill cycles
- confirm `position_rollup_source` is usually cached or otherwise cheap enough

Acceptance:

- no routine cycle shows recurring full rebuild behavior
- restart behavior does not leave the writer in repeated fallback mode
- any remaining heavy equity cost is either negligible or explicitly documented
- bootstrap-only full rebuild reasons are acceptable if they clear after initial stabilization

### Work Package B: QuantOps secondary contract decision

Goal:
Decide where explicit stable/live/display contracts are still worth adding.

Tasks:

- review `analytics/equity-history`
- review `analytics/execution-latest`
- review `analytics/execution-planner-latest`
- classify each route as:
  - promote contract
  - keep freshness metadata only
  - keep debug/feed semantics only

Acceptance:

- secondary route policy is explicit
- no important mixed summary remains ambiguous
- read-model-first direction stays intact

Recommended initial classification:

- promote first:
  - `analytics/equity-history`
- review but likely keep as feed/debug-style:
  - `analytics/execution-latest`
  - `analytics/execution-planner-latest`
- do not force into full stable/live/display just for uniformity:
  - `risk` summary surfaces
  - `monitoring` summary surfaces

### Work Package C: Regression and docs lock-in

Goal:
Prevent SprintH regressions after the final cleanup.

Tasks:

- add regression coverage for any newly promoted secondary contract
- add writer closeout notes to docs
- update runbook with writer log interpretation guidance
- update roadmap docs so “done” versus “optional” is explicit

Acceptance:

- the remaining SprintH behavior is documented
- the current architecture direction is protected by tests

## Recommended Priority

Do the remaining work in this order:

1. V12 writer final profiling
2. secondary route contract decision
3. regression and docs lock-in

This order keeps the highest-value uncertainty first while avoiding unnecessary contract churn.

## Route Classification Guidance

Use this rule when deciding whether to extend stable/live/display.

Promote the full contract when the response is:

- operator-facing
- summary-shaped
- likely to mix a stable baseline with fresher overlay data

Do not promote the full contract when the response is:

- a pure feed
- a debug/provenance surface
- already sufficiently explained by:
  - `dataStatus`
  - `dataSource`
  - `isStale`
  - freshness metadata

## Current Recommendation

The present recommendation for SprintH is:

- do not reopen broad timeout work
- do not move frontend back toward truth-heavy request paths
- do not expand cache layers into hidden recompute paths
- finish with writer verification, selective contract cleanup, and regression/doc lock-in

## Related Docs

- [timeout-roadmap.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/timeout-roadmap.md)
- [timeout-improvement-pr-summary.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/timeout-improvement-pr-summary.md)
- [architecture-read-models.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/architecture-read-models.md)
- [api-summary-contracts.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/api-summary-contracts.md)
- [writer-observability.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/writer-observability.md)
- [ops-runbook.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/ops-runbook.md)
