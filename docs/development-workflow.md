# Development Workflow

This document captures the workflow that proved effective during the timeout-improvement work.

It is intended as a reusable engineering workflow for future performance, stability, and read-path changes in this repo.

## Core Principle

Do not jump directly into deep architectural rewrites.

Use this order:

1. reproduce the real problem
2. apply low-risk containment
3. add observability
4. make structural fixes
5. stabilize tests and docs

This kept the system usable while deeper changes were still underway.

## Step 1: Reproduce On The Real Stack

The most important rule is:

- do not trust unit tests alone for timeout and startup problems

For this codebase, the real issues were only fully visible when checking:

- browser behavior
- real local startup scripts
- backend logs
- repeated page loads
- first-hit vs repeated-hit timings

Useful checks:

- open Overview / Portfolio / Execution and wait
- inspect browser network
- inspect:
  - [quantops.log](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/test_bundle/artifacts/recheck_start_logs_2/quantops.log)
  - [frontend-start.log](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/test_bundle/artifacts/recheck_start_logs_2/frontend-start.log)

## Step 2: Contain With Low-Risk Changes First

Before changing writer semantics, it was effective to first reduce user-facing pain with:

- stale-first behavior
- short TTL cache
- in-flight coalescing
- startup sequencing
- delayed warmup
- reduced prefetch
- reduced live-feed window size

This gave immediate relief without risking truth/accounting behavior.

Rule:

- if a problem can be made tolerable safely, do that before deep redesign

## Step 3: Add Observability Before Deep Refactors

Structural changes became much safer once the system could explain itself.

The most useful additions were:

- writer metrics
- freshness metadata
- build status
- full rebuild reasons
- explicit stable/live/display contracts

Examples:

- `writer_cycles.jsonl`
- `cycle_duration_ms`
- `fills_scanned_positions`
- `fills_scanned_equity`
- `position_row_write_duration_ms`
- `full_rebuild_reason`
- `source_snapshot_time`
- `rebuilt_at`
- `data_freshness_sec`
- `build_status`

Rule:

- if you cannot explain why a request is slow, do not start a large rewrite yet

## Step 4: Separate Truth From Display

One of the most important design lessons was to keep these distinct:

- truth/accounting representation
- user-facing display representation

Examples from this repo:

- V12 truth tracks positions by:
  - `symbol`
  - `strategy_id`
  - `alpha_family`
- normal Portfolio display aggregates by symbol for readability

Likewise:

- stable summary totals are not the same thing as recent live feed data

Rule:

- preserve truth at the backend layer
- simplify only at the UI/presentation layer

## Step 5: Make Mixed Responses Explicit

When a response merges stable data and live overlay, it must be explicit.

The pattern that worked best was:

- `stable_value`
- `live_delta`
- `display_value`

This made it possible to explain:

- why the displayed number changed
- whether the source was stale or fresh
- whether there was a live overlay

Rule:

- never hide mixed semantics behind a generic `latest` field when operator trust matters

## Step 6: Prefer Read Models Over Heavy Direct Reads

The long-term improvement came from moving main GUI paths toward stable summary/read-model style endpoints.

Examples:

- `overview_summary_latest`
- `portfolio_metrics_latest`
- `execution/view/latest`
- `runtime/status`

This was better than trying to protect every heavy path with ad-hoc cache alone.

Rule:

- use cache as a thin optimization layer
- use read-model routes as the main stable read surface

## Step 7: Improve Writer Behavior Incrementally

Deep writer changes were safest when done in small stages:

1. observe current cost
2. add versioned snapshot behavior
3. add fill watermark
4. avoid no-fill rewrites
5. update only affected rows
6. reuse same-cycle data inside writer flow

This was much safer than replacing the entire writer path in one step.

Rule:

- move from `O(total)` toward `O(delta)` in steps, with regression coverage at each step

## Step 8: Verify Start And Stop Paths As First-Class Features

Startup and shutdown scripts are not peripheral. They are part of the working system.

Important lesson from Windows:

- killing only the listener port is not always enough

Failed starts can leave:

- non-listening `uvicorn`
- `next`
- parent `cmd.exe`
- file locks on DuckDB

So stop logic must account for:

- port listeners
- child service processes
- launcher parent processes when needed

Rule:

- every start script should have a verified stop path

## Step 9: Treat Old Sprint Tests As Active Contracts

A test file being old does not mean it is obsolete.

If CI still runs it, it is part of the current contract.

This repo’s regression packs made that very clear:

- `truth`
- `stale`
- `debug`

Large refactors must include:

- reviewing which older tests still matter
- updating expectations where the external contract changed
- deleting tests only when the contract is intentionally retired

Rule:

- if CI runs it, maintain it

## Step 10: Document While The Reasoning Is Fresh

The most useful docs after the work were:

- runbook
- summary contract doc
- read-model architecture
- writer observability guide
- portfolio display semantics

Without these, later changes would require rediscovering the same reasoning.

Rule:

- after major stabilization work, convert operational knowledge into docs immediately

## Recommended Workflow For Similar Future Work

Use this sequence:

1. reproduce on the real stack
2. add low-risk mitigation
3. add observability
4. measure again
5. implement structural change in small pieces
6. verify with targeted tests
7. verify on the real stack
8. update CI-facing regression tests
9. document final contracts and operations

## Anti-Patterns To Avoid

- trying to solve a production-style timeout problem with unit tests only
- rewriting writer logic before measuring where time is actually spent
- mixing stable totals and live windows without explicit contract fields
- trusting port-based stop logic alone on Windows
- assuming old sprint tests are obsolete without checking CI
- using cache as a substitute for proper read-model design

## Related Docs

- [timeout-roadmap.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/06_playbooks/timeout-roadmap.md)
- [ops-runbook.md](/C:/work_data/pyWorkSpace\QuantOpsV12\QuantOps_github/docs/ops-runbook.md)
- [api-summary-contracts.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/07_interfaces/api-summary-contracts.md)
- [architecture-read-models.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/02_architecture/architecture-read-models.md)
- [writer-observability.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/02_architecture/writer-observability.md)
