# Hardening Handover Manifest Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet follows:

- `docs/Hardening_architect_handoff_plan.md`
- `docs/Hardening_evidence_snapshot_plan.md`

The repo can already expose live status, save evidence snapshots, and generate architect-facing handoff markdown.
The next step is to add one manifest surface that points to the current handover entrypoints and verifier set.

## First Manifest Invariant

```text
current hardening handover state
-> can be read from one manifest
-> points to the key docs, scripts, and system surfaces
-> reports whether the saved snapshot and architect handoff are available
-> gives the next thread a single machine-readable entrypoint
```

## Scope

This packet should cover:

- key docs
- key verifier scripts
- key hardening surfaces
- latest runtime run id
- snapshot availability
- architect handoff availability
- reference-file existence check

## Implementation Artifact

- `GET /system/hardening-handover-manifest`

## Verification Artifact

- `test_bundle/scripts/verify_hardening_handover_manifest.py`

## Why This Packet Matters

The repo now has enough hardening surfaces that the next resume point should not depend on memory.
This packet fixes that by making one manifest the canonical starting point for resume, review, and architect check-ins.

## Verification Command

```text
python test_bundle/scripts/verify_hardening_handover_manifest.py --json
```

Expected shape:

- `status = ok`
- no failures
- manifest references existing docs and scripts
- snapshot and architect handoff both show available
