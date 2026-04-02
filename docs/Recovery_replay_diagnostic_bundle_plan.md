# Recovery Replay Diagnostic Bundle Plan

Date: `2026-04-01`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet extends:

- `docs/Recovery_replay_confidence_plan.md`
- `docs/Operator_diagnostic_bundle_plan.md`

The first recovery/replay packet already proved that ingest and replay paths reach the same recovery result.
The next operator-facing step is to expose the latest live reconciliation mismatch and recovery chain as one diagnostic bundle.

## First Recovery/Replay Diagnostic Invariant

```text
latest live reconciliation mismatch
-> can be inspected through one recovery/replay bundle
-> shows the reconciliation source path
-> shows incident, recovery, and final runtime state together
-> preserves the same parity summary for ingest and replay paths
```

## Scope

This packet should cover:

- latest live order
- latest live fill
- reconciliation event chain
- linked incident row
- runtime audit chain
- final trading state after recovery
- explicit parity summary
- explicit operator readiness / mismatch summary

## Implementation Artifact

- `GET /system/recovery-replay-diagnostic-bundle`

## Verification Artifact

- `test_bundle/scripts/verify_recovery_replay_diagnostic_bundle.py`

## Why This Packet Matters

The repo already proves recovery/replay determinism at test level.
This packet proves that the same confidence is operator-visible and can be pulled without manually joining reconciliation, incident, audit, and runtime state surfaces.

## Verification Command

```text
python test_bundle/scripts/verify_recovery_replay_diagnostic_bundle.py --json
```

Expected shape:

- `status = ok`
- no failures
- ingest and replay bundles share the same parity outcome
- only `source_path` differs
