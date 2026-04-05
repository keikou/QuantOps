# Runtime Regression Triage

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `initial_runtime_regression_playbook`

## Purpose

Use this playbook when the local stack appears to have regressed and you need to decide quickly whether the issue is real, stale, or lane-breaking.

## When To Use

Use this when:

- a health route fails unexpectedly
- a previously working runtime surface now looks broken
- logs, UI behavior, and docs state disagree

## Steps

1. confirm the current repo state from `../11_reports/current_status.md`
2. confirm the current task from `../04_tasks/current.md`
3. verify the local stack startup path from `../09_runtime_ops/current_runtime_ops.md`
4. inspect runtime and correlation logs via `../09_runtime_ops/incident_and_tracing.md`
5. run the narrowest relevant verifier first
6. only classify the issue as a regression if repo truth and verifier output both support it

## Evidence To Prefer

- health endpoints
- runtime logs
- correlation ids
- verifier failures

## Evidence To Distrust

- stale thread memory
- old architect assumptions without current-status confirmation
- isolated UI impressions without runtime evidence

## Rule

A runtime problem is not lane-reopening evidence until the current repo truth and a narrow verifier both point to the same break.
