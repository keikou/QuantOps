# Resume Quickcheck Runner Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet follows:

- `docs/Resume_bundle_index_plan.md`
- `docs/Resume_automation_helper_plan.md`

The repo already has a resume bundle index and individual verifiers.
The next step is a thin runner that executes the lightweight resume sanity verifiers in one command and summarizes pass/fail state.

## First Runner Invariant

```text
current resume bundle
-> can be quickchecked with one local command
-> runs the lightweight resume verifiers
-> reports per-check status and overall status
```

## Scope

- one local runner script
- lightweight resume sanity verifiers only
- compact JSON summary

## Implementation Artifact

- `test_bundle/scripts/run_resume_quickcheck.py`

## Verification Artifact

- `test_bundle/scripts/verify_resume_quickcheck_runner.py`
