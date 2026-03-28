# Phase4 Alpha Factory Plan

Date: `2026-03-29`
Repo: `QuantOps_github`
Branch: `main`
Status: `planning`

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

This may end up being the hardest closure invariant for Phase4.

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

### P4-D

```text
champion-challenger decisions are persisted and produce a measurable selected winner
```

### P4-E

```text
governed alpha state can influence later runtime-facing selection or deployment state
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
2. ask architect to judge current completeness and closure gaps
3. implement first proof tests for governance-state transitions
4. add live verification script
5. close with completion memo if architect confirms closure

## Exit Condition

Phase4 should only move to `COMPLETE` when the repo can show:

- explicit proof tests
- live verification
- architect re-judgment
- final completion memo

in the same way Phase1, Phase2, and Phase3 were closed.
