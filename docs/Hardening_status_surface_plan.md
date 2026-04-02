# Hardening Status Surface Plan

Date: `2026-04-01`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet follows:

- `docs/Operator_diagnostic_bundle_plan.md`
- `docs/Recovery_replay_diagnostic_bundle_plan.md`
- `docs/Post_Phase7_hardening_status_update_2026-04-01.md`

The repo now has multiple hardening packets and multiple operator-facing bundles.
The next step is to expose a single status surface that tells whether the currently available repo evidence is sufficient to call each packet operator-ready.

## First Hardening Status Invariant

```text
current repo evidence
-> can be summarized as packet-level readiness
-> reuses the operator and recovery/replay bundles
-> reports which hardening packets are currently ready
-> reports whether the track is fully operator-ready as a whole
```

## Scope

This packet should cover readiness for:

- recovery / replay confidence
- cross-phase acceptance
- audit / provenance
- research registration mirroring
- research governance mirroring
- runtime config provenance
- deploy provenance
- runtime governance linkage
- multi-cycle acceptance
- operator diagnostic bundle
- recovery/replay diagnostic bundle

## Implementation Artifact

- `GET /system/hardening-status`

## Verification Artifact

- `test_bundle/scripts/verify_hardening_status_surface.py`

## Why This Packet Matters

The architect-facing status doc is static.
This packet turns the same hardening story into a live machine-readable surface that an operator or reviewer can pull from the running repo state.

## Verification Command

```text
python test_bundle/scripts/verify_hardening_status_surface.py --json
```

Expected shape:

- `status = ok`
- no failures
- `overall.all_ready = true`
- all listed packets report `ready = true`
