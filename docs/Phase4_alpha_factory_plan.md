# Phase4 Alpha Factory Plan

Date: `2026-03-29`
Repo: `QuantOps_github`
Branch: `main`
Status: `in_progress`

## Objective

Start `Phase4: Alpha Factory` as the next closure track after:

- `Phase1 Truth Layer = COMPLETE`
- `Phase2 Execution Reality = COMPLETE`
- `Phase3 Portfolio Intelligence = COMPLETE`

Phase4 should not be treated as "more alphas exist".

It should be treated as:

```text
Alpha production, evaluation, governance, and promotion are closed as a system loop.
```

## Working Closure Definition

Phase4 is complete only when this loop is explicitly closed:

```text
alpha idea / generation
-> feature + dataset registration
-> experiment + validation
-> model candidate registration
-> ranking / promotion / shadow / rollback governance
-> live review / decay tracking
-> champion-challenger decision
-> next alpha selection / deployment state
```

## Current Starting Point

The repo already contains meaningful Phase4 components:

- alpha registry and alpha library routes
- generated/tested/evaluated alpha flow
- research-factory dataset / feature / experiment / validation / model registration
- promotion policy
- live model review
- alpha decay monitor
- rollback policy
- champion-challenger service
- research dashboard and alpha-factory dashboard

This means Phase4 starts from a real implementation base, not from zero.

## Existing Evidence

### Alpha factory API coverage

- `apps/v12-api/tests/test_phaseh_sprint4_api.py`

Current evidence:

- `/alpha/generate`
- `/alpha/test`
- `/alpha/evaluate`
- `/alpha/overview`
- `/alpha/registry`
- `/alpha/ranking`
- `/alpha/library`
- `/dashboard/alpha-factory`

### Research-factory governance coverage

- `apps/v12-api/tests/test_phaseh_sprint2_api.py`
- `apps/v12-api/tests/test_phaseh_sprint3_api.py`

Current evidence:

- dataset / feature / experiment / validation / model registration
- promotion evaluation
- live review
- alpha decay
- rollback evaluation
- champion-challenger run
- governance overview
- research dashboard

### Core services already present

- `apps/v12-api/ai_hedge_bot/research_factory/service.py`
- `apps/v12-api/ai_hedge_bot/research_factory/promotion_policy.py`
- `apps/v12-api/ai_hedge_bot/research_factory/rollback_policy.py`
- `apps/v12-api/ai_hedge_bot/research_factory/live_model_review.py`
- `apps/v12-api/ai_hedge_bot/research_factory/alpha_decay_monitor.py`
- `apps/v12-api/ai_hedge_bot/learning/champion_challenger.py`

## Architect-Guided Priority

Current architect judgment:

```text
Phase4 = PARTIALLY COMPLETE
```

Architect's closure framing:

```text
Alpha Factory = alpha lifecycle loop fully closed
```

Architect's first required invariant:

```text
alpha -> evaluation -> ranking -> portfolio inclusion -> execution impact
```

Architect's hardest gap:

```text
runtime deployment linkage
```

## What Is Still Not Proven

These are the likely closure gaps:

### 1. Closed production loop

Need proof that:

```text
generated/tested/evaluated alpha state
actually changes later governance or deployment state
under explicit invariants
```

### 2. Ranking / promotion loop closure

Need proof that:

```text
validation and live-review outcomes
change promotion / shadow / rollback decisions deterministically
```

### 3. Candidate-to-live state transition proof

Need proof that:

```text
candidate -> approved/shadow/live/rolled_back
is not just endpoint existence,
but a coherent governed state machine
```

### 4. Portfolio/runtime integration proof

Need proof that:

```text
selected/promoted alpha artifacts
can influence runtime signals or allocation inputs
```

This is now the architect-confirmed hardest closure invariant for Phase4.

## Proposed Invariants

### P4-A

```text
new alpha candidate generation increases the governed candidate set
```

### P4-B

```text
validation metrics affect ranking and promotion outcomes
```

### P4-C

```text
bad live-review / decay / rollback signals change governance state explicitly
```

Status:

- now implemented and proof-tested

### P4-D

```text
champion-challenger decisions are persisted and produce a measurable selected winner
```

### P4-E

```text
governed alpha state can influence later runtime-facing selection or deployment state
```

This should be treated as the first proof target, not a late optional one.

Status:

- now implemented and proof-tested

## Current Closed Proofs

The repo can now show:

```text
P4-E: promoted alpha -> runtime signal / portfolio / execution linkage
P4-C: runtime result / decay evidence -> governance-visible state transition
```

That means Phase4 has moved beyond component coverage.

The likely next proof target is:

```text
updated governance state
-> next-cycle selection / deployment reuse
```

## Deliverables

### 1. Status packet for architect

Suggested file:

- `docs/Phase4_status_for_architect.md`

### 2. First proof test packet

Suggested file:

- `apps/v12-api/tests/test_phase4_alpha_factory_closure.py`

### 3. Live verification script

Suggested file:

- `test_bundle/scripts/verify_phase4_alpha_factory_closure.py`

### 4. Completion memo

Suggested file:

- `docs/Phase4_alpha_factory_completion_final.md`

## Recommended Execution Order

1. inventory what is already implemented
2. use architect judgment as the starting Definition of Done
3. implement first proof tests for runtime-linkage and governance-state transitions
4. re-ask architect for the next closure invariant
5. add live verification script / completion memo when closure is confirmed

## Exit Condition

Phase4 should only move to `COMPLETE` when the repo can show:

- explicit proof tests
- live verification
- architect re-judgment
- final completion memo

in the same way Phase1, Phase2, and Phase3 were closed.
