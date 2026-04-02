# Docs Operating Index

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `proposed_docs_operating_index`

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

1. `../01_context/`
2. `../03_plans/`
3. `../04_tasks/`
4. `../05_workflows/`
5. `../07_interfaces/`
6. `../09_runtime_ops/`
7. `../11_reports/`

Until the migration is complete, the closest current files are:

1. `../Development for AI.md`
2. `../Auto_resume_handover_2026-04-02.md`
3. `../Architect_alignment_resume_memo_2026-04-02.md`
4. `../Post_Phase7_hardening_architect_report_2026-04-02.md`
5. `../Hardening_architect_handoff_latest.md`
6. `../Resume_operator_packet_latest.md`

## Current Focus

- hardening slice is sufficiently complete for the current branch stage
- do not reopen completed hardening packets unless a real regression is found
- next likely lane is `Execution Reality`
- current branch remains `codex/post-phase7-hardening`

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
