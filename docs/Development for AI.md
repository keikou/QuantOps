# Development for AI

## Purpose

This document is the fast-start guide for any AI agent, thread, or reviewer that needs to continue development in this repository without rediscovering the project structure and operating rules from scratch.

Use this as the first document to read before making design or implementation decisions.

## Project Overview

This repo contains a three-layer local trading operations stack:

- V12
  - truth, runtime, writer, snapshots, correctness-critical state
- QuantOps API
  - read-model aggregation, operator-facing contracts, stale-first behavior, cache/coalescing
- QuantOps Frontend
  - UI presentation of stable summary and live feed

The working architectural rule is:

- V12: correctness-first
- QuantOps API: contract-and-latency-first
- frontend: stable summary and live feed must stay separated

Do not mix truth semantics and display semantics casually.

## Current State

As of the latest closeout state:

- broad timeout mitigation is complete
- main GUI paths no longer reproduce the earlier timeout waves in normal local verification
- `analytics/equity-history` was also aligned to the explicit stable/display contract style
- writer no-fill cycles and restart-followed samples were rechecked on the real stack
- SprintH is complete
- `Phase1 Truth Layer = COMPLETE`
- `Phase2 Execution Reality = COMPLETE`
- `Phase3 Portfolio Intelligence = COMPLETE`
- `Phase4 Alpha Factory = COMPLETE`
- `Phase5 Risk / Guard OS = COMPLETE`

Completion references:

- [SprintH_completion_report.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/SprintH_completion_report.md)
- [sprinth-finish-plan.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/sprinth-finish-plan.md)
- [Sprint6H_truth_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Sprint6H_truth_completion_final.md)
- [Phase2_execution_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Phase2_execution_completion_final.md)
- [Phase3_allocation_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Phase3_allocation_completion_final.md)
- [Phase4_alpha_factory_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Phase4_alpha_factory_completion_final.md)
- [Phase5_risk_guard_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Phase5_risk_guard_completion_final.md)
- [After_Sprint6H_Roadmap_from_Architect.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/After_Sprint6H_Roadmap_from_Architect.md)

## Read These Docs First

Read in this order when starting fresh:

1. [After_Sprint6H_Roadmap_from_Architect.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/After_Sprint6H_Roadmap_from_Architect.md)
2. [Sprint6H_truth_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Sprint6H_truth_completion_final.md)
3. [Phase2_execution_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Phase2_execution_completion_final.md)
4. [Phase3_allocation_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Phase3_allocation_completion_final.md)
5. [Phase4_alpha_factory_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Phase4_alpha_factory_completion_final.md)
6. [Phase5_risk_guard_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Phase5_risk_guard_completion_final.md)
7. [SprintH_completion_report.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/SprintH_completion_report.md)
8. [correlation-logging-guide.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/correlation-logging-guide.md)
9. [development-rules-v12-vs-quantops.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/development-rules-v12-vs-quantops.md)
10. [development-workflow.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/development-workflow.md)
11. [architecture-read-models.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/architecture-read-models.md)
12. [api-summary-contracts.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/api-summary-contracts.md)
13. [ops-runbook.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/ops-runbook.md)
14. [dev-startup.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/dev-startup.md)
15. [ci_regression_packs.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/ci_regression_packs.md)
16. [chatgpt-codex-cowork.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/chatgpt-codex-cowork.md)

Read these when touching specific areas:

- writer behavior:
  - [writer-observability.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/writer-observability.md)
- portfolio UI semantics:
  - [portfolio-display-semantics.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/portfolio-display-semantics.md)
- broader background:
  - [timeout-roadmap.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/timeout-roadmap.md)
  - [timeout-improvement-pr-summary.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/timeout-improvement-pr-summary.md)
- timeout, incident, and page-access tracing:
  - [correlation-logging-guide.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/correlation-logging-guide.md)
  - [ops-runbook.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/ops-runbook.md)

## Quick Mental Model

### V12

V12 owns:

- fills
- orders
- positions
- equity
- runtime truth
- snapshot generation
- watermark processing
- writer cost and contention behavior

If a change affects accounting or truth, it usually belongs here.

### QuantOps API

QuantOps API owns:

- summary/read-model aggregation
- stale-first behavior
- short TTL cache
- in-flight coalescing
- operator-facing response contracts
- freshness and provenance fields

If a change affects response shape, read-path latency, or frontend-facing semantics, it usually belongs here.

### Frontend

Frontend should:

- consume explicit contracts
- prefer `display_value`
- show freshness separately
- keep stable summary and live feed distinct

Frontend should not invent hidden truth semantics.

## Key Contract Rules

When a response mixes stable summary and live overlay, prefer:

- `stable_value`
- `live_delta`
- `display_value`

Also preserve:

- `build_status`
- `source_snapshot_time`
- `rebuilt_at`
- `data_freshness_sec`

Do not hide mixed semantics behind a generic `latest` field if operator understanding matters.

## Recommended Development Process

Use this sequence:

1. reproduce on the real stack
2. apply low-risk containment first if needed
3. add or inspect observability
4. make structural fixes in small steps
5. run targeted tests
6. verify on the real stack
7. update regression coverage
8. update docs

This project repeatedly validated that workflow.

## Fast Local Startup

Preferred startup order:

1. `start_v12_api.cmd`
2. `start_quantops_api.cmd`
3. `start_frontend.cmd`

Or use:

- `run_all.cmd`

Health endpoints:

- V12: `http://127.0.0.1:8000/system/health`
- QuantOps API: `http://127.0.0.1:8010/api/v1/health`
- frontend: `http://127.0.0.1:3000/`

Always use `127.0.0.1`, not `localhost`, for local checks in this repo.

Stop scripts are first-class and should be used when needed:

- `stop_all.cmd`
- `stop_all_prod.cmd`
- `stop_v12_api.cmd`
- `stop_quantops_api.cmd`
- `stop_frontend.cmd`

## Verification Shortcuts

Useful checks:

- QuantOps regression packs:
  - `powershell -ExecutionPolicy Bypass -File test_bundle/scripts/run_quantops_api_regression_pack.ps1 -Pack all`
- local startup smoke:
  - `powershell -ExecutionPolicy Bypass -File test_bundle/scripts/run_local_startup_smoke.ps1`
- frontend build:
  - `npm run build` in `apps/quantops-frontend`

When doing performance or timeout work, do not trust unit tests alone. Check the real stack, logs, and first-hit versus repeated-hit behavior.

## Writer Verification

If you touch V12 writer or truth logic, inspect:

- `runtime/logs/writer_cycles.jsonl`
- `runtime/logs/orchestrator_runs.jsonl`

Important fields:

- `fills_scanned_positions`
- `fills_scanned_equity`
- `position_row_write_duration_ms`
- `position_history_rows_written`
- `full_rebuild_reason`
- `equity_full_rebuild_reason`

Healthy no-fill cycle:

- zero fill scans
- zero row rewrite
- zero history writes
- no rebuild reason

## Correlation Logging

Frontend page-view and API error telemetry now has a first-pass correlation path:

- frontend emits page and client error events to:
  - `apps/quantops-api/runtime/logs/frontend_events.jsonl`
- QuantOps API request middleware writes:
  - `apps/quantops-api/runtime/logs/quantops_requests.jsonl`
- QuantOps API forwards correlation headers to V12
- V12 request middleware writes:
  - `apps/v12-api/runtime/logs/v12_requests.jsonl`

Primary keys used to correlate events:

- `trace_id`
- `request_id`
- `session_id`
- `page_path`

Header flow:

- frontend request headers:
  - `X-Request-Id`
  - `X-Client-Request-Id`
  - `X-Trace-Id`
  - `X-Session-Id`
  - `X-Page-Path`
- QuantOps API returns:
  - `X-Request-Id`
  - `X-Trace-Id`
- QuantOps API forwards the same trace/session/page headers to V12

This is the intended debugging path when you need to answer:

- which page view triggered an API call
- which QuantOps request led to a V12 upstream call
- whether a frontend error and backend failure share the same `trace_id`

Use [correlation-logging-guide.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/correlation-logging-guide.md) first when the problem statement is phrased like:

- "Overview opened slowly"
- "Portfolio timed out once"
- "frontend showed timeout but API later looked healthy"
- "which user action caused this backend error"

That guide is the shortest one-page walkthrough with concrete examples and command snippets.

Current limitation:

- `frontend-start.log` is still only a process startup log, not a user interaction log
- button-level telemetry is not yet generalized; page views, client errors, and API errors are the current baseline

## Current Known Safe Direction

Do:

- prefer read-model and summary routes over heavy truth reads
- keep cache as a thin optimization layer
- keep truth and display separate
- preserve explicit freshness/build metadata
- treat old CI tests as active contracts if CI still runs them

Do not:

- reintroduce heavy truth recompute into normal read paths
- add GUI-specific display logic into V12 truth paths
- assume old sprint tests are obsolete without checking CI
- use cache as a substitute for proper read-model design

## AI Role Guidance

For multi-AI or multi-thread work, the most effective split is:

- implementation agent:
  - inspect repo
  - patch code
  - run tests/builds
  - verify real-stack behavior
  - update docs after implementation
- design/review agent:
  - compare alternatives
  - identify risks
  - challenge architecture decisions
  - help decompose next sprint work

Keep design advice grounded in actual code and logs.

## Where To Start For Common Tasks

### New roadmap work after Phase5

Read:

- [After_Sprint6H_Roadmap_from_Architect.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/After_Sprint6H_Roadmap_from_Architect.md)
- [Phase5_risk_guard_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Phase5_risk_guard_completion_final.md)

Then treat:

- post-Phase5 hardening
- later `Phase6 Live Trading`

as the next roadmap tracks, not Phase1/2/3/4/5 reopening.

### New backend feature

Read:

- [development-rules-v12-vs-quantops.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/development-rules-v12-vs-quantops.md)
- [architecture-read-models.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/architecture-read-models.md)
- [api-summary-contracts.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/api-summary-contracts.md)

Then decide first whether the change belongs in V12 or QuantOps API.

### Performance or timeout issue

Read:

- [development-workflow.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/development-workflow.md)
- [timeout-roadmap.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/timeout-roadmap.md)
- [writer-observability.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/writer-observability.md)
- [ops-runbook.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/ops-runbook.md)

### Frontend contract or display change

Read:

- [api-summary-contracts.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/api-summary-contracts.md)
- [portfolio-display-semantics.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/portfolio-display-semantics.md)

### Startup, stop, or operational issue

Read:

- [dev-startup.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/dev-startup.md)
- [ops-runbook.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/ops-runbook.md)

## Final Rule

If you are unsure what to do next:

1. inspect the current code
2. inspect the real logs
3. verify which contract is currently live
4. prefer the smallest change that preserves the project’s current architecture direction

That approach has been consistently safer and faster in this repo than starting with a broad rewrite.
