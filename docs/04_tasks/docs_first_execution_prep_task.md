# Task: Docs-First Execution Prep

Date: `2026-04-06`
Status: `reusable`

## Goal

Prepare an implementation or docs task by deriving the current lane, active task, and verifier path from docs before reading code deeply.

## Why Now

The repo is now treating docs as the operating system for AI and human execution, so the first loop should be explicit and reusable.

## Inputs

- `../10_agent/ai_docs_operating_loop.md`
- `../03_plans/current.md`
- `../04_tasks/current.md`
- the active task file under `../04_tasks/`
- the closest supporting docs by layer

## Steps

1. read the docs-first operating loop
2. identify the current lane and active task from canonical docs
3. identify the closest supporting docs needed for the task
4. name the narrowest relevant verifier before implementation starts
5. only then move into code inspection or edits

## Outputs

- one explicit task route
- one explicit verifier route
- one short implementation starting point that does not depend on thread memory

## Non-Goals

- full implementation of the lane packet itself
- broad architecture review
- reopening completed checkpoint lanes without evidence

## Completion Check

- the current task, current lane, and current verifier path can be stated from docs alone
