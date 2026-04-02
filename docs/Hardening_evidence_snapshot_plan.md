# Hardening Evidence Snapshot Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet follows:

- `docs/Hardening_status_surface_plan.md`
- `docs/Operator_diagnostic_bundle_plan.md`
- `docs/Recovery_replay_diagnostic_bundle_plan.md`

The repo already exposes live hardening status and live diagnostic bundles.
The next step is to save those surfaces as one fixed evidence snapshot that can be shared, restored, or reviewed later without recomputing context manually.

## First Snapshot Invariant

```text
current hardening state
-> can be exported as one saved snapshot
-> preserves hardening-status plus both diagnostic bundles
-> keeps track and branch expectations explicit
-> can be loaded back as a stable evidence packet
```

## Scope

This packet should cover:

- current hardening status payload
- current operator diagnostic bundle
- current recovery/replay diagnostic bundle
- generated timestamp
- track metadata
- snapshot save and latest read surfaces

## Implementation Artifacts

- `POST /system/hardening-evidence-snapshot/save`
- `GET /system/hardening-evidence-snapshot/latest`

## Verification Artifact

- `test_bundle/scripts/verify_hardening_evidence_snapshot.py`

## Why This Packet Matters

The status surface is live and ephemeral.
This packet turns that state into a durable repo-local evidence packet suitable for architect check-ins, handover, and later regression review.

## Verification Command

```text
python test_bundle/scripts/verify_hardening_evidence_snapshot.py --json
```

Expected shape:

- `status = ok`
- no failures
- saved snapshot and latest snapshot agree on core fields
- snapshot contains hardening status and both diagnostic bundles
