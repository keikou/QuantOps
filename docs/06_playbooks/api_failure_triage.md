# API Failure Triage

Date: `2026-04-06`
Repo: `QuantOps_github`
Status: `initial_api_failure_playbook`

## Purpose

Use this playbook when an API route fails, times out, or returns a payload that no longer matches the expected contract.

## When To Use

Use this when:

- a `/system/*` or other operator-facing endpoint returns an error
- an endpoint starts timing out after a recent change
- a route returns a shape that conflicts with `07_interfaces`

## Steps

1. confirm the expected route and payload from `../07_interfaces/current_contracts.md`
2. confirm the current lane and task from `../03_plans/current.md` and `../04_tasks/current.md`
3. inspect the narrowest relevant route implementation
4. reproduce the failure with the smallest possible local call
5. run the narrowest relevant verifier before broad debugging
6. classify the issue as contract drift, implementation bug, runtime setup issue, or stale docs

## Evidence To Prefer

- direct endpoint responses
- verifier output
- route-local logs
- current contract docs

## Evidence To Distrust

- assumptions from older lane packets
- broad recollection of how the route used to behave
- unrelated runtime noise from other surfaces

## Rule

Treat an API failure as a local contract or runtime problem first, not as evidence that a completed lane must be replayed.
