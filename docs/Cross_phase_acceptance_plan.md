# Cross Phase Acceptance Plan

Date: `2026-03-29`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `System Reliability Hardening Track`
Status: `in_progress`

## Purpose

This packet is the second hardening lane after recovery / replay confidence.

Target chain:

```text
truth -> execution -> allocation -> alpha -> guard -> live -> self-improving
```

The goal is to verify that one governed runtime scenario can pass across these phase boundaries with attributable evidence, without reopening any Phase1 to Phase7 closure claim.

## Scope

This packet should focus on one acceptance-oriented scenario that proves:

- runtime truth evidence is materialized after an accepted cycle
- execution and allocation artifacts stay attributable to the same cycle
- promoted alpha governance changes the next cycle in an observable way
- guard state explicitly blocks or allows live intent
- live order and reconciliation evidence remain consistent with guard state
- self-improving evidence remains attributable to the promoted alpha / model path

## First Acceptance Invariant

```text
governed self-improving promotion
-> changes next-cycle dominant alpha and allocation weight
-> produces execution and truth evidence for the accepted cycle
-> guard state blocks live while halted and allows live send after resume
-> live reconciliation completes with attributable records
```

This first invariant does not replace the recovery / replay packet.
It complements it by showing the post-Phase7 system can still behave as one accepted operating chain across the closed phases.

## Existing Repo Evidence

The repo already contains closure-grade proofs for the underlying phase behaviors in:

- `apps/v12-api/tests/test_phase2_execution_loop_closure.py`
- `apps/v12-api/tests/test_phase3_allocation_loop_closure.py`
- `apps/v12-api/tests/test_phase4_alpha_factory_closure.py`
- `apps/v12-api/tests/test_phase5_risk_guard_closure.py`
- `apps/v12-api/tests/test_phase6_live_trading_closure.py`
- `apps/v12-api/tests/test_phase7_self_improving_closure.py`

This packet is not reopening those closures.
It is checking that the already-closed behaviors still compose into one cross-phase acceptance path.

## First Deliverables

### 1. Local verification script

Artifact:

- `test_bundle/scripts/verify_cross_phase_acceptance.py`

Purpose:

- run a baseline paper cycle
- apply a governed self-improving `keep` decision for a registered model / alpha pair
- run a second paper cycle and verify the promoted alpha changes the accepted chain
- verify truth, allocation, execution, and bridge artifacts exist for that accepted cycle
- verify guard halt blocks live intent
- verify resume re-enables live send and matched reconciliation

### 2. Future expansion

Possible later expansions:

- multi-cycle acceptance bundles
- recovery / replay reuse inside the acceptance scenario
- operator-facing diagnostic bundle checks
- attribution links from live outcome back into governed self-improving follow-up evidence

## Verification Command

```text
python test_bundle/scripts/verify_cross_phase_acceptance.py --json
```

Expected shape:

- `status = ok`
- no failures
- promoted alpha affects the next accepted cycle
- truth / execution / live artifacts all exist and are internally consistent

## Architect Alignment Rule

The first invariant above is derived from existing architect-approved hardening direction and current repo behavior.

Reopen architect alignment in chat `Roadmapと進捗管理2` only if:

- this invariant proves unstable in repo reality
- the preferred first invariant needs to shift away from governed promotion plus accepted live path
- a real regression suggests the hardening lane ordering is wrong
