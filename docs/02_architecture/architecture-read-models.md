# Read Model Architecture

This document explains the current read-path architecture after the timeout-improvement work.

## Problem Statement

The original timeout waves were caused by a mix of:

- heavy truth-table reads
- heavy writer activity
- read/write contention on the same DuckDB files
- GUI paths that mixed stable summary data with fresh event data without an explicit contract

The fix direction was not "add more cache everywhere". The fix direction was:

- make writer work more incremental
- introduce thinner summary/read-model style routes
- keep caches as response optimization, not hidden truth recompute

## Layer Model

The current architecture is best understood as four layers.

### 1. Truth layer

This is the authoritative state in V12.

Examples:

- `execution_fills`
- `position_snapshots_latest`
- `position_snapshots_history`
- `equity_snapshots`
- `execution_quality_snapshots`

Key property:

- correctness first

### 2. Read-model / summary layer

These routes exist to serve stable GUI summaries cheaply.

Examples:

- V12 `/portfolio/overview-summary/latest`
- V12 `/portfolio/metrics/latest`
- V12 `/execution/view/latest`
- V12 `/runtime/status`

Key property:

- cheap, stable reads built from already-available summary state

### 3. QuantOps aggregation layer

QuantOps API translates upstream V12 summary responses into frontend-facing contracts.

Examples:

- `/api/v1/dashboard/overview`
- `/api/v1/portfolio/overview`
- `/api/v1/portfolio/metrics`
- `/api/v1/execution/view/latest`
- `/api/v1/command-center/runtime/latest`

Key property:

- presentation-friendly contracts
- stale-first behavior where appropriate
- coalescing of repeated reads

### 4. Frontend presentation layer

The frontend distinguishes:

- stable summary
- live feed

Examples:

- Overview cards vs secondary feeds
- Portfolio totals vs positions table
- Execution stable summary vs recent runs/issues/fills/orders

Key property:

- do not pretend recent feeds are stable totals

## Stable Summary vs Live Feed

The main design rule is:

- stable totals come from summary/read-model paths
- recent events come from live feed paths

### Stable summary examples

- dashboard overview
- portfolio overview
- portfolio metrics
- execution summary
- runtime latest

### Live feed examples

- recent fills
- recent orders
- runtime runs
- runtime issues

## Contract Style

Where stable and live values are combined, the response should be explicit:

- `stable_value`
- `live_delta`
- `display_value`

Supporting metadata:

- `build_status`
- `source_snapshot_time`
- `rebuilt_at`
- `data_freshness_sec`

This keeps values explainable when:

- stale cache is served
- live overlay exists
- fallback path was used

## Cache Responsibility

Cache is not the source of truth.

Cache is used only to:

- absorb repeated reads
- avoid burst-triggered rebuilds
- serve stale values immediately while refresh is deferred

Good cache targets:

- summary/read-model routes
- feed responses with small recent windows

Bad cache target:

- hidden heavy truth recompute behind a normal request path

## Why Read Models Matter

Without a summary/read-model layer:

- Overview and Portfolio read paths hit heavier upstream logic
- Execution summary needs multiple upstream calls
- startup warmup and first paint compete with writer activity

With summary/read-model routes:

- the main GUI paths read from a smaller, more stable contract
- QuantOps can apply stale-first consistently
- frontend can separate stable and live semantics cleanly

## Current Main Read Models

### Portfolio

- `/portfolio/overview-summary/latest`
- `/portfolio/metrics/latest`

### Execution

- `/execution/view/latest`

### Runtime

- `/runtime/status`

These are not full materialized tables in every case. Some are lightweight summary routes over stabilized upstream state. The important point is that the GUI no longer depends on heavier truth reads for normal first paint.

## Remaining Direction

The main remaining refinement is:

- keep equity path incremental and cheap
- extend explicit contracts only where secondary mixed responses still need them

The broad architectural direction should remain:

- truth for correctness
- read models for stable GUI reads
- live feeds for recent windows

## Related Docs

- [timeout-roadmap.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/06_playbooks/timeout-roadmap.md)
- [api-summary-contracts.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/07_interfaces/api-summary-contracts.md)
- [timeout-improvement-pr-summary.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/06_playbooks/timeout-improvement-pr-summary.md)
