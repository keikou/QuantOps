# API Summary Contracts

This document defines the common response contract used by the major QuantOps summary endpoints after the timeout-improvement work.

The goal is to make cached, stable, and mixed live values explicit instead of hiding them behind ambiguous "latest" fields.

## Why This Exists

The GUI now separates:

- stable summary
- live feed

Some endpoints return only stable summary values.
Some endpoints return a stable value plus a small live overlay.

To make that explicit, summary endpoints use a shared set of fields where appropriate:

- `stable_value`
- `live_delta`
- `display_value`
- `build_status`
- `source_snapshot_time`
- `rebuilt_at`
- `data_freshness_sec`

## Field Definitions

### `stable_value`

The value derived from the stable summary/read-model path.

Examples:

- cached runtime summary
- cached overview summary
- cached portfolio metrics summary

This should be the operator-traceable baseline value.

### `live_delta`

The incremental adjustment applied on top of `stable_value`, when the endpoint mixes in fresher live information.

Examples:

- a recent state overlay
- a live run-state adjustment

If there is no live overlay, this should be `null`, empty, or a zero-like value depending on the endpoint shape.

### `display_value`

The value the UI should normally display.

This is usually:

- `stable_value` when there is no live overlay
- `stable_value + live_delta` when the endpoint intentionally merges them

Frontend should prefer `display_value` over reconstructing it locally.

### `build_status`

Explains how the response was built.

Observed values in this codebase include:

- `live`
- `degraded_live`
- `fresh_cache`
- `stale_cache`

Meaning:

- `live`
  - built from the current live path
- `degraded_live`
  - live path succeeded, but with a fallback or degraded source
- `fresh_cache`
  - returned from fresh cached response data
- `stale_cache`
  - stale value returned immediately while refresh is deferred/backgrounded

### `source_snapshot_time`

The timestamp of the underlying upstream snapshot or summary source.

This is not the same as response rebuild time.

### `rebuilt_at`

The timestamp when the QuantOps response payload was last built or refreshed.

Use this together with `source_snapshot_time`:

- `source_snapshot_time`
  - how old the upstream data is
- `rebuilt_at`
  - how recently this response object was rebuilt

### `data_freshness_sec`

Human-readable freshness distance in seconds between "now" and the relevant source snapshot.

This is the easiest operator-facing freshness field.

## Endpoint Families

### Overview summary

Primary endpoint:

- `/api/v1/dashboard/overview`

Behavior:

- stable summary endpoint
- may be served from live, fresh cache, or stale cache
- exposes freshness/build metadata
- exposes `stable_value` / `display_value` contract for major KPI sections

### Portfolio summary

Primary endpoints:

- `/api/v1/portfolio/overview`
- `/api/v1/portfolio/metrics`
- `/api/v1/portfolio/positions`

Behavior:

- overview and metrics are summary-style
- positions are a read-style list response with freshness metadata
- `display_value` should be treated as the UI-facing value for KPI blocks

### Execution summary

Primary endpoint:

- `/api/v1/execution/view/latest`

Behavior:

- combines planner/state summary into one response
- exposes stable/live/display semantics for operator-facing execution summary fields

### Runtime summary

Primary endpoint:

- `/api/v1/command-center/runtime/latest`

Behavior:

- summary-style response
- can return live, fresh cache, stale cache, or degraded live
- exposes stable/display contract for UI presentation

### Live feed endpoints

Examples:

- `/api/v1/execution/orders`
- `/api/v1/execution/fills`
- `/api/v1/command-center/runtime/runs`
- `/api/v1/command-center/runtime/issues`

Behavior:

- these are recent-window/live-feed endpoints
- they carry freshness/build metadata
- they are not the same as stable summary endpoints

These should not be treated as authoritative portfolio/runtime totals.

### Runtime triage workflow fields

Runtime live-feed/detail payloads may also expose lightweight operator workflow state.

Run-level fields:

- `review.review_status`
- `review.acknowledged`
- `review.operator_note`
- `review.reviewed_by`
- `review.reviewed_at`

Issue-bucket fields:

- `acknowledged`
- `acknowledgement.acknowledged_by`
- `acknowledgement.acknowledged_at`
- `acknowledgement.note`

Mutation endpoints:

- `POST /api/v1/command-center/runtime/runs/{run_id}/review`
- `POST /api/v1/command-center/runtime/issues/{diagnosis_code}/acknowledge`

Rules:

- this workflow state is operator-facing metadata, not truth
- it should be attached in QuantOps API, not inferred in frontend
- it should remain read/write-light and must not pull heavy truth recompute onto the request path

## UI Rules

### Use `display_value` by default

For major KPI cards and primary summary labels:

- use `display_value` if present
- fall back to stable/raw only when the endpoint has no explicit display contract

### Show freshness separately

UI should not encode freshness into the value itself.

Instead, use:

- `build_status`
- `source_snapshot_time`
- `rebuilt_at`
- `data_freshness_sec`

in observability or status UI.

### Keep live feed separate from stable totals

Do not mix:

- recent fills/orders/runs/issues

with:

- stable portfolio/runtime/execution totals

unless the endpoint explicitly defines the merge via:

- `stable_value`
- `live_delta`
- `display_value`

## Debugging Guidance

When a displayed value looks wrong, inspect these in order:

1. `display_value`
2. `stable_value`
3. `live_delta`
4. `build_status`
5. `source_snapshot_time`
6. `rebuilt_at`
7. `data_freshness_sec`

This usually tells you whether the issue is:

- stale data
- a live overlay
- a fallback path
- or a wrong frontend merge assumption

## Scope

This contract is already used across the major GUI summary surfaces:

- Overview
- Portfolio
- Execution
- Runtime

It may be extended later to remaining secondary summary routes if needed.
