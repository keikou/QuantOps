# Resume And Docs State Drift

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `initial_resume_docs_drift_playbook`

## Purpose

Use this playbook when conversations, handoff docs, and repo truth no longer align cleanly.

## When To Use

Use this when:

- an old handoff says one lane is active but `current.md` says another
- a conversation suggests replaying completed work
- a root-level doc still reads like the canonical truth after the folder entrypoints have moved on

## Steps

1. treat `../00_index/README.md` as the top routing source
2. confirm `../03_plans/current.md`, `../04_tasks/current.md`, and `../11_reports/current_status.md`
3. check whether the mismatch is:
   - historical context only
   - stale canonical routing
   - actual repo-state contradiction
4. prefer adding or updating canonical route notes before making physical moves
5. only reopen a completed lane if a verifier or code truth shows a real contradiction

## Typical Fixes

- add a `Canonical Route` note to a root-level doc
- update a folder `README.md` or `current.md`
- update `current_docs_migration_map.md`
- add a task file if the work is now active enough to deserve an executable task spec

## Rule

A stale document is a docs maintenance issue by default, not an execution replay instruction.
