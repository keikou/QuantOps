# Resume Automation Helper Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet follows:

- `docs\Auto_resume_handover_2026-04-02.md`
- `docs\Hardening_handover_manifest_plan.md`

The repo already has a manifest, saved evidence snapshot, and generated architect handoff.
The next step is a local helper that reads those entrypoints and prints the current resume context in one command.

## First Helper Invariant

```text
current hardening resume state
-> can be pulled with one local helper command
-> starts from the hardening handover manifest
-> reads latest snapshot and architect handoff
-> reports the key verifier scripts to run next
```

## Scope

This packet should cover:

- manifest load
- latest evidence snapshot load
- latest architect handoff load
- key doc paths
- key verifier script paths
- compact machine-readable summary

## Implementation Artifact

- `test_bundle/scripts/resume_hardening_helper.py`

## Verification Artifact

- `test_bundle/scripts/verify_resume_automation_helper.py`

## Why This Packet Matters

The updated auto-resume doc points to the manifest as the primary entrypoint.
This helper makes that flow operational by reducing resume context gathering to one command.

## Verification Command

```text
python test_bundle/scripts/verify_resume_automation_helper.py --json
```

Expected shape:

- `status = ok`
- no failures
- helper output includes manifest, snapshot, handoff, and verifier references
