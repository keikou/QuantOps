# Current Runtime Operations

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `current_runtime_ops_guidance`

## Core Runtime Entry

For current runtime operations, start with:

- `../00_index/README.md`
- `../10_agent/ai_docs_operating_loop.md`
- `./supporting_runtime_ops.md`
- `../03_plans/current.md`
- `../04_tasks/current.md`
- `../ops-runbook.md`
- `../dev-startup.md`

## Current Operating Rules

- use `127.0.0.1`, not `localhost`
- prefer the repo startup/stop scripts over ad-hoc process handling
- verify health routes before debugging deeper behavior
- use correlation and runtime logs before forming root-cause claims

## Current Service Surfaces

- V12 API: `http://127.0.0.1:8000/system/health`
- QuantOps API: `http://127.0.0.1:8010/api/v1/health`
- frontend: `http://127.0.0.1:3000/`

## Current Recommended Startup Path

1. `start_v12_api.cmd`
2. `start_quantops_api.cmd`
3. `start_frontend.cmd`

Or:

- `run_all.cmd`

## Current Recommended Stop Path

- `stop_all.cmd`
- `stop_all_prod.cmd`
- service-specific `stop_*.cmd` scripts when a partial restart is intended

## Current Runtime Reminder

The repo is not in a broad timeout-mitigation firefight anymore.

So current runtime work should usually be:

- docs-routed investigation
- targeted verification
- targeted incident analysis
- targeted next-lane work

not broad re-debugging of already closed system slices unless a regression is found.

## Current Runtime Start Rule

Before debugging runtime deeply:

1. confirm the current lane and task from docs
2. identify the exact surface that looks wrong
3. choose the narrowest relevant verifier
4. only then widen into startup, logs, or stack-wide checks
