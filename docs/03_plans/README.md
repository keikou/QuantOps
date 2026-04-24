# Plans Index

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `canonical_plans_entrypoint`

## Purpose

This folder is the canonical entrypoint for plan and roadmap documents.

It answers:

- which plan is historical
- which plan is still active
- what the current next-lane planning question is

## Current Canonical Files

1. `./current.md`
2. `./roadmap.md`
3. `./historical_plans.md`
4. `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_checkpoint_v1.md`
5. `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_architect_status_update_2026-04-05.md`

## Planning Rule

Treat old plans as context, not as automatically active instructions.

The repo has already moved beyond:

- initial hardening proposal
- initial cross-phase acceptance start decision
- hardening packet sequencing
- initial `DRI`, `LCC`, and `MPI` packet construction

The current planning job is to reselect the next lane after the completed `AAE v1` checkpoint freeze.

## Current Default Direction

- freeze completed `AAE v1`
- select the next top-level lane from current repo truth

Historical note:

- `Execution Reality` was the first post-hardening default direction before later lane checkpoints were completed

## Alternative Directions

- no stale pre-`SERI` or pre-`AAE` direction should be treated as active by default

## Guardrails

- do not reopen completed hardening packets as if they are still planned work
- do not infer current priority from older plan docs without checking `current.md`
- do not rename the current track to `Phase8` unless architect changes guidance
- route root-level plan artifacts through `historical_plans.md` before moving them physically
