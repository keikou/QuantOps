# Rollback Decision Path

Date: `2026-04-06`
Repo: `QuantOps_github`
Status: `initial_rollback_decision_playbook`

## Purpose

Use this playbook when a change appears risky enough that you need to decide whether to contain, revert, or continue under observation.

## When To Use

Use this when:

- a fresh change breaks a current verifier
- a runtime issue impacts an operator-facing surface
- docs, code, and runtime evidence suggest a real regression rather than stale state drift

## Steps

1. confirm whether the failing behavior is on the current active task path
2. run the narrowest relevant verifier and capture the concrete failure
3. decide whether the issue is:
   - docs-only drift
   - local environment noise
   - bounded implementation regression
   - lane-level risk
4. prefer the smallest containment move that restores truth:
   - doc correction
   - targeted code fix
   - feature/path disablement
   - revert of the newest offending change
5. update the canonical docs state after the containment decision

## Outputs

- one explicit containment decision
- one explicit reason for not reopening unrelated completed lanes
- one doc writeback reflecting the decision

## Non-Goals

- panic rollback of unrelated work
- replay of previously completed checkpoints without fresh evidence
- broad architectural redesign during incident handling

## Rule

Rollback is justified only when verifier-backed repo truth shows the newest change is materially worse than the last known good state.
