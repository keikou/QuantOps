# Recovery Replay Confidence Plan

Date: `2026-03-29`
Repo: `QuantOps_github`
Branch: `main`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This is the first concrete lane under post-Phase7 hardening.

Architect priority for the hardening track is:

```text
Recovery / Replay Confidence
```

The goal is to strengthen trust that:

- the same live evidence produces the same reconciliation result
- recovery and resume behavior remains deterministic
- ingest and replay paths do not diverge in incident, audit, or guard outcome

## Scope

This lane should focus on:

- live reconciliation mismatch handling
- incident creation and resolution continuity
- halt and resume behavior after mismatch
- path-independent replay confidence
- durable audit continuity across recovery

## First Hardening Invariant

```text
same live evidence
-> same reconciliation outcome
-> same incident and guard state
-> same recovery and resume result
regardless of ingest vs replay path
```

## Existing Repo Evidence

The repo already has closure-grade proofs in:

- `apps/v12-api/tests/test_phase6_live_trading_closure.py`
- `apps/v12-api/ai_hedge_bot/services/live_trading_service.py`
- `docs/Phase6_live_trading_completion_final.md`

That means this lane is not reopening Phase6.
It is widening confidence and making the replay/recovery behavior easier to verify operationally.

## First Deliverables

### 1. Local verification script

Artifact:

- `test_bundle/scripts/verify_recovery_replay_confidence.py`

Purpose:

- run an ingest mismatch flow
- run an equivalent replay mismatch flow
- compare reconciliation, incident, audit, and final trading state

### 2. Follow-up proof expansion

Possible later artifact:

- broader pytest coverage for multi-order or multi-symbol replay confidence

### 3. Cross-phase acceptance handoff

When this lane is stable, feed its results into:

- `docs/Cross_phase_acceptance_plan.md`

## Verification Command

```text
python test_bundle/scripts/verify_recovery_replay_confidence.py --json
```

Expected shape:

- `status = ok`
- no failures
- ingest and replay artifact snapshots match on the covered surfaces

## Next Likely Expansion

After the first script is stable, expand into:

- repeated recovery/resume cycles
- more than one live order in the same scenario
- broader audit lineage checks
- cross-phase acceptance scenarios that include recovery and replay reuse
