# Resume Bundle Refresh Runner Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet follows:

- `docs/Resume_quickcheck_runner_plan.md`
- `docs/Hardening_evidence_snapshot_plan.md`

The repo already has saved resume artifacts and a quickcheck runner.
The next step is a refresh runner that regenerates the saved resume artifacts in one command.

## First Runner Invariant

```text
current resume bundle
-> can be refreshed with one local command
-> regenerates snapshot, architect handoff, and operator packet
-> reports per-step status and overall status
```

## Scope

- one local refresh runner
- artifact regeneration only
- compact JSON summary

## Implementation Artifact

- `test_bundle/scripts/run_resume_bundle_refresh.py`

## Verification Artifact

- `test_bundle/scripts/verify_resume_bundle_refresh_runner.py`
