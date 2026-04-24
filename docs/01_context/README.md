# Context Index

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `canonical_context_entrypoint`

## Purpose

This folder is the canonical entrypoint for project context and working assumptions.

It answers:

- what this repo is
- what stage the repo is currently in
- what background a human or AI should understand before acting

## Current Canonical Files

1. `./project_state.md`
2. `./working_assumptions.md`
3. `./supporting_context_docs.md`
4. `../Development for AI.md`
5. `../After_Sprint6H_Roadmap_from_Architect.md`
6. `../chatgpt-codex-cowork.md`

## Context Rule

Use `context` to understand the repo and current stage.
Do not use it as the only source for active priorities.

For active priorities, continue from:

- `../03_plans/current.md`
- `../04_tasks/current.md`

## Current Stage Summary

- `Phase1` through `Phase7` remain complete
- current branch work is still under `codex/post-phase7-hardening`
- the current hardening/resume slice is already treated as sufficiently complete
- `Meta Portfolio Intelligence v1` first checkpoint is complete
- `Strategy Evolution / Regime Adaptation Intelligence v1` is checkpoint-complete through `SERI-05`
- `Autonomous Alpha Expansion / Strategy Generation Intelligence v1` is checkpoint-complete through `AAE-05`
- next top-level lane is currently under reselection after the completed `AAE v1` checkpoint
- current execution mode is `docs-first`, then `code`, then `narrow verifier`, then `docs writeback`

Historical note:

- `Execution Reality`, then `SERI`, then `AAE` were earlier post-hardening next-lane candidates, but none of them is now the active next lane

## Guardrails

- do not infer that an older roadmap document is still the current task
- do not restart completed hardening packets from context docs alone
- use context docs for orientation, not for replaying old execution order
