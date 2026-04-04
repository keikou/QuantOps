# Current Development Guide

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `current_dev_guidance`

## Core Working Rule

Use the repo in this order:

1. read the canonical indexes first
2. confirm the current plan and task
3. inspect the real code and the real stack
4. implement the smallest high-signal change
5. run the narrowest relevant verifier
6. write back the new truth into docs

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

- `Strategy Evolution / Regime Adaptation Intelligence`

Historical note:

- `Execution Reality` was the earlier next-lane default before the repo advanced through later completed checkpoints

## Read Next For Details

- `../development-rules-v12-vs-quantops.md`
- `../05_workflows/dev-flow.md`
- `../01_context/working_assumptions.md`
- `../03_plans/current.md`
- `../04_tasks/current.md`
