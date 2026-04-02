# Runtime Config Provenance Plan

Date: `2026-04-01`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet addresses one of the main gaps from:

- `docs/Audit_provenance_gap_review.md`

The goal is to preserve the effective runtime configuration that produced a run, so a successful or failed runtime cycle can be tied back to:

- settings-derived behavior
- mode policy
- price/runtime configuration

## First Runtime Config Provenance Invariant

```text
runtime run start
-> captures effective config snapshot
-> computes stable config fingerprint
-> persists the same config provenance
in run_started audit and latest_orchestrator_run checkpoint
```

## Scope

This packet should capture:

- effective mode
- app config values relevant to runtime execution
- selected settings values that materially affect runtime behavior
- mode policy
- truth / price runtime config

This packet does not yet persist:

- deploy SHA
- image digest
- external secrets fingerprints

Those can follow in later provenance work.

## Persistence Targets

The first implementation should write config provenance into:

- `audit_logs` for `event_type=run_started`
- `runtime_checkpoints` for `checkpoint_name=latest_orchestrator_run`
- runtime API response from `/runtime/run-once`

## Verification Artifact

- `test_bundle/scripts/verify_runtime_config_provenance.py`

The verifier should:

- run one runtime cycle
- read the `run_started` audit payload
- read the `latest_orchestrator_run` checkpoint payload
- confirm both contain `config_provenance`
- confirm fingerprints match
- confirm selected snapshot fields match expected runtime configuration

## Why This Packet Is The Right Next Step

Research and governance mirroring already improved audit continuity.
The next missing operator question is:

```text
which effective runtime configuration produced this run?
```

This packet makes that question locally answerable.

## Verification Command

```text
python test_bundle/scripts/verify_runtime_config_provenance.py --json
```

Expected shape:

- `status = ok`
- no failures
- `run_started` and checkpoint config fingerprints match
