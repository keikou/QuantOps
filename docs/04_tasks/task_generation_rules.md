# Task Generation Rules

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `task_generation_rules`

## Purpose

This file explains how to generate new task files consistently.

## Generation Rule

Use `1 task = 1 file` when:

- the task can be completed as one bounded implementation or docs unit
- the task has a specific output surface
- the task needs explicit non-goals to avoid lane sprawl

## Naming Rule

Use this shape:

```text
<short_task_name>_<YYYY-MM-DD>.md
```

Prefer names that describe the executable unit, not the whole lane.

## Minimum Required Sections

- `Goal`
- `Why Now`
- `Inputs`
- `Steps`
- `Outputs`
- `Non-Goals`
- `Completion Check`

## Preferred Task Types

- lane packet implementation
- verifier addition or verification pass
- interface contract hardening
- runtime regression investigation
- docs-state alignment

## Rule

If a task cannot be expressed clearly with these sections, it is probably still a plan item rather than an executable task.
