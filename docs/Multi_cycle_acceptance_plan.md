# Multi Cycle Acceptance Plan

Date: `2026-04-01`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet extends:

- `docs/Cross_phase_acceptance_plan.md`
- `docs/Runtime_governance_linkage_plan.md`

The single-cycle acceptance path is already verified.
The next hardening step is to prove that acceptance confidence survives across more than one governed runtime cycle.

## First Multi-Cycle Acceptance Invariant

```text
governed self-improving promotion
-> changes the next accepted cycle
-> remains attributable across consecutive accepted cycles
-> keeps runtime governance linkage, truth, execution, and checkpoint evidence consistent
```

## Scope

This first packet should cover:

- baseline paper cycle
- self-improving keep decision for a registered model / alpha pair
- first promoted paper cycle
- second promoted paper cycle

Across those cycles, the verifier should confirm:

- promoted alpha remains selected on the intended symbol
- runtime governance linkage remains explicit
- execution bridge remains explicit and internally coherent
- truth state remains stable even when later cycles produce no new delta
- acceptance does not collapse after the first promoted cycle

## Verification Artifact

- `test_bundle/scripts/verify_multi_cycle_acceptance.py`

## Why This Packet Matters

Single-cycle acceptance proves one handoff.
Multi-cycle acceptance proves the handoff is stable enough to persist into the next accepted cycle without silently dropping attribution or execution continuity.

## Verification Command

```text
python test_bundle/scripts/verify_multi_cycle_acceptance.py --json
```

Expected shape:

- `status = ok`
- no failures
- promoted alpha and governance linkage survive across both promoted cycles
