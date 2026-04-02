# Operator Diagnostic Bundle Plan

Date: `2026-04-01`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet follows:

- `docs/Runtime_governance_linkage_plan.md`
- `docs/Multi_cycle_acceptance_plan.md`
- `docs/Deploy_provenance_plan.md`

The hardening track already proves that runtime cycles can carry:

- cross-phase acceptance
- governance linkage
- config provenance
- deploy provenance

The next operator-facing step is to expose those proofs in one diagnostic surface that can be read without manually joining multiple endpoints and tables.

## First Operator Diagnostic Bundle Invariant

```text
latest accepted runtime cycle
-> can be inspected through one operator bundle
-> preserves run/cycle identity across runtime, bridge, portfolio, and checkpoint views
-> includes governance linkage plus config/deploy provenance
-> reports whether the bundle is internally consistent enough for operator use
```

## Scope

This packet should cover:

- latest runtime run identity
- latest execution bridge state
- latest execution quality summary
- latest portfolio overview summary
- latest portfolio diagnostics
- latest signal snapshot
- latest orchestrator checkpoint payload
- runtime governance linkage
- config provenance
- deploy provenance
- explicit consistency summary

## Implementation Artifact

- `GET /system/operator-diagnostic-bundle`

## Verification Artifact

- `test_bundle/scripts/verify_operator_diagnostic_bundle.py`

## Why This Packet Matters

The previous packets proved that evidence exists.
This packet proves that an operator can pull the evidence as one coherent bundle and immediately see whether the current run is attributable, replayable, and deployment-identifiable.

## Verification Command

```text
python test_bundle/scripts/verify_operator_diagnostic_bundle.py --json
```

Expected shape:

- `status = ok`
- no failures
- `consistency.operator_ready = true`
- config, deploy, and governance linkage are visible in one bundle
