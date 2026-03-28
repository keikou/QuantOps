# Phase7 Self-Improving System Plan

Date: `2026-03-29`
Repo: `QuantOps_github`
Branch: `main`
Status: `planning`

## Objective

Start `Phase7: Self-Improving System` as the next closure track after:

- `Phase1 Truth Layer = COMPLETE`
- `Phase2 Execution Reality = COMPLETE`
- `Phase3 Portfolio Intelligence = COMPLETE`
- `Phase4 Alpha Factory = COMPLETE`
- `Phase5 Risk / Guard OS = COMPLETE`
- `Phase6 Live Trading = COMPLETE`

Phase7 should not mean only:

```text
models can be retrained
```

It should mean:

```text
observed live and research outcomes
-> deterministic evaluation / attribution
-> governed strategy or alpha update decision
-> controlled deployment or rollback
-> measured next-cycle improvement
```

## Working Closure Definition

Phase7 is complete only when this loop is explicitly closed:

```text
result evidence
-> attribution / evaluation
-> governed improvement decision
-> model / alpha / allocation update
-> deployment into runtime
-> next-cycle measured outcome
-> deterministic keep / reduce / retire / reinforce decision
```

## Existing Repo Evidence

The repo already contains strong prerequisites:

- Phase4 alpha lifecycle and governance closure
- Phase5 guard / recovery / policy closure
- Phase6 live routing, reconciliation, incident, and recovery closure
- experiment, validation, promotion, rollback, and live review tables in runtime store
- research-factory and model review surfaces

Relevant references:

- `apps/v12-api/ai_hedge_bot/research_factory/`
- `apps/v12-api/ai_hedge_bot/research_factory/governance_state.py`
- `apps/v12-api/ai_hedge_bot/research_factory/live_model_review.py`
- `apps/v12-api/ai_hedge_bot/services/live_trading_service.py`
- `apps/v12-api/ai_hedge_bot/data/storage/runtime_store.py`

## Likely Closure Invariants

### P7-CLOSE-1

```text
same observed performance evidence
-> deterministic evaluation / attribution verdict
-> explicit improve / keep / reduce / retire recommendation
```

### P7-CLOSE-2

```text
governed improvement decision
-> deterministic model or alpha state transition
-> runtime-visible deployment or exclusion
```

### P7-CLOSE-3

```text
updated model or alpha state
-> changed runtime behavior
-> measurable next-cycle effect
```

### P7-CLOSE-4

```text
same evidence across equivalent replay / review paths
-> same improvement decision
-> same deployment / rollback outcome
```

## Deliverables

### 1. Architect status packet

Suggested file:

- `docs/Phase7_status_for_architect.md`

### 2. First proof test packet

Suggested file:

- `apps/v12-api/tests/test_phase7_self_improving_closure.py`

### 3. Verification script

Suggested file:

- `test_bundle/scripts/verify_phase7_self_improving_closure.py`

### 4. Completion memo

Suggested file:

- `docs/Phase7_self_improving_completion_final.md`

## Recommended Execution Order

1. get architect judgment for exact closure definition
2. inventory what is already deterministic versus still advisory
3. implement first proof for `same evidence -> deterministic improvement verdict`
4. add governed deployment / exclusion proof
5. add next-cycle effect proof
6. add replay-path determinism proof
7. add verification script
8. close with completion memo after architect re-judgment

## Exit Condition

Phase7 should move to `COMPLETE` only when the repo can show:

- explicit proof tests
- governed improvement decisions that change runtime state
- measurable next-cycle consequences
- architect re-judgment
- final completion memo

## Architect Initial Verdict

Initial architect judgment:

```text
Phase7 = NOT STARTED AS A CLOSED PHASE
```

Interpretation:

- the repo has strong prerequisites for self-improvement
- but it does not yet have a proven closure packet
- advisory review, experiment, and promotion surfaces are not enough by themselves

Architect-confirmed closure framing:

```text
result evidence
-> deterministic evaluation / attribution
-> explicit governed improvement decision
-> update or deploy into runtime
-> next-cycle measured outcome
-> deterministic keep / reduce / retire / reinforce decision
```

Architect-confirmed `Phase7-CLOSE-1` starting point:

```text
result evidence
-> deterministic evaluation
-> explicit governed improvement decision
```

Architect-confirmed initial hardest gap:

```text
hardest gap = update deploy -> next-cycle measured outcome linkage
```
