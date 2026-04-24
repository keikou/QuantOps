# Docs Operating Index

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `active_docs_operating_index`

## Purpose

This index is the shared entrypoint for both humans and AI agents.

The goal is not to move the entire `docs/` tree at once.
The goal is to make the current flat `docs/` set understandable now, then migrate gradually toward a clearer operating structure.

## Target Structure

```text
docs/
├─ 00_index/
├─ 01_context/
├─ 02_architecture/
├─ 03_plans/
├─ 04_tasks/
├─ 05_workflows/
├─ 06_playbooks/
├─ 07_interfaces/
├─ 08_dev_guides/
├─ 09_runtime_ops/
├─ 10_agent/
├─ 11_reports/
└─ 99_archive/
```

## Why This Structure

- `00_index` is the single entrypoint
- `plans` and `tasks` stay separate
- `workflows` make next-step reasoning explicit for AI and humans
- `interfaces` covers APIs, schemas, contracts, and events
- `reports` acts as the current state store
- migration can happen incrementally without losing orientation

## Human Entry

Read in this order:

1. `../01_context/`
2. `../02_architecture/`
3. `../03_plans/`
4. `../08_dev_guides/`
5. `../09_runtime_ops/`
6. `../11_reports/`

Until the migration is complete, the closest current files are:

1. `../Development for AI.md`
2. `../After_Sprint6H_Roadmap_from_Architect.md`
3. `../Post_Phase7_hardening_architect_report_2026-04-02.md`
4. `../development-workflow.md`
5. `../ops-runbook.md`
6. `../Resume_bundle_completion_status_2026-04-02.md`

## AI Agent Entry

Read in this order:

1. `../10_agent/`
2. `../03_plans/`
3. `../04_tasks/`
4. `../07_interfaces/`
5. `../09_runtime_ops/`
6. `../02_architecture/`
7. `../11_reports/`

Until the migration is complete, the closest current files are:

1. `../10_agent/README.md`
2. `../10_agent/ai_docs_operating_loop.md`
3. `../03_plans/current.md`
4. `../04_tasks/current.md`
5. `../07_interfaces/current_contracts.md`
6. `../11_reports/current_status.md`

## Current Focus

- `Phase1` through `Phase7` are complete
- hardening/resume plus `Execution Reality`, `Governance -> Runtime Control`, `Portfolio Intelligence`, `Alpha / Strategy Selection Intelligence`, `Research / Promotion Intelligence`, `System-Level Learning / Feedback Integration`, `Policy Optimization`, `Deployment / Rollout Intelligence`, `Live Capital Control`, and `Meta Portfolio Intelligence` first checkpoints are complete
- `Strategy Evolution / Regime Adaptation Intelligence v1` is checkpoint-complete through `SERI-05`
- `Autonomous Alpha Expansion / Strategy Generation Intelligence v1` is checkpoint-complete through `AAE-05`
- do not reopen completed closure or checkpoint work unless a real regression is found
- current top-level planning state is `next_lane_reselection_after_aae_v1`
- `AAE v1` is frozen unless a real regression is found
- current AI operating mode is `docs-first`, then `code`, then `narrow verifier`, then `docs writeback`
- current branch remains `codex/post-phase7-hardening`
- latest pushed commit in canonical docs is no longer the stale early-`SERI` tip

## Immediate Migration Rule

Do not start by physically moving every existing file.

Use this order instead:

1. establish `00_index`
2. map current files to target folders
3. decide canonical files per target folder
4. move only the highest-value files first
5. leave historical reports in place until references are updated

## Canonical Mapping Reference

The working map for current files to target folders is:

- `./current_docs_migration_map.md`

## Guardrails

- do not create duplicate truth in old and new paths
- do not rename `Phase1` to `Phase7` closure artifacts casually
- do not move hardening handoff docs until the replacement entrypoints are stable
- prefer adding `index` and `map` before mass file movement

## Single-Sentence Summary

```text
Use docs/00_index/README.md as the shared human/AI entrypoint, keep the current flat docs set readable through a migration map, and migrate gradually toward context / architecture / plans / tasks / workflows / interfaces / runtime_ops / reports.
```
