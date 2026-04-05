# AI Docs Operating Loop

Date: `2026-04-06`
Repo: `QuantOps_github`
Status: `current_ai_docs_operating_loop`

## Purpose

This file defines the shortest docs-only loop an AI agent should follow before acting.

## Loop

1. read `../00_index/README.md`
2. read `../03_plans/current.md`
3. read `../04_tasks/current.md`
4. read the active task file under `../04_tasks/`
5. read the closest supporting docs for the task layer:
   - `../07_interfaces/` for contract work
   - `../09_runtime_ops/` for runtime work
   - `../02_architecture/` for structure or ownership questions
6. inspect code only after the docs route is clear
7. run the narrowest relevant verifier
8. write new truth back into the canonical docs before stopping

## Escalation Rule

If the docs route and repo truth disagree:

1. trust the verifier and the code over stale thread memory
2. update the canonical docs route
3. only then decide whether a completed lane must be reopened

## Shared Role Split

- ChatGPT app: decision framing, architect discussion, prioritization
- Codex: repo inspection, implementation, verification, docs writeback

## Rule

If an AI agent cannot describe the current task, current lane, and current verifier path from docs alone, it should keep reading docs before changing code.
