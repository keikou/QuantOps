# Current Development Guide

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `current_dev_guidance`

## Core Working Rule

Use the repo in this order:

1. read the canonical indexes first
2. confirm the current plan and task
3. confirm the docs-first operating loop
4. inspect the real code and the real stack
5. implement the smallest high-signal change
6. run the narrowest relevant verifier
7. write back the new truth into docs

Current startup route:

1. `../00_index/README.md`
2. `../10_agent/ai_docs_operating_loop.md`
3. `../03_plans/current.md`
4. `../04_tasks/current.md`
5. the active task file

## Layer Rule

Keep the system split clear:

- `V12` = correctness-first truth/runtime layer
- `QuantOps API` = contract-and-latency-first aggregation layer
- `frontend` = stable summary and live feed presentation layer

Do not mix truth semantics and display semantics casually.

## Current Delivery Rule

The repo is no longer in a "prove hardening exists" stage.

That means:

- do not restart `Cross-Phase Acceptance`
- do not re-package resume docs as the main task
- do not reopen `Phase1` to `Phase7` closure claims unless a real regression is found

If work continues, prefer starting the next lane beyond hardening/resume.

## Default Next Lane

- no stale default lane should override `docs/03_plans/current.md`
- current boundary is `AAE v1 checkpoint freeze`
- next lane must be selected from current repo truth before new packet work starts

Historical note:

- `Execution Reality`, then `SERI`, then `AAE` were earlier next-lane defaults before the repo advanced through later completed checkpoints

## Read Next For Details

- `../development-rules-v12-vs-quantops.md`
- `../05_workflows/dev-flow.md`
- `../01_context/working_assumptions.md`
- `../10_agent/ai_docs_operating_loop.md`
- `../03_plans/current.md`
- `../04_tasks/current.md`
