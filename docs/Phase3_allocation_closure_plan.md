# Phase3 Allocation Closure Plan

Date: `2026-03-29`
Repo: `QuantOps_github`
Branch: `main`
Status: `in_progress`

## Objective

Close `Phase3: Portfolio Intelligence` at the same rigor level used to close:

- Sprint6H truth completion
- Phase2 execution reality

Architect's current classification is:

```text
Portfolio Intelligence = PARTIALLY COMPLETE
```

The missing piece is not basic optimizer existence.

The missing piece is:

```text
Allocation Loop Closure Proof
```

## Closure Definition

Phase3 is complete only when this loop is provably closed:

```text
alpha -> optimizer -> weights -> execution -> result -> feedback -> reallocation
```

This must be true:

- causally
- measurably
- reproducibly
- under explicit contract tests

## Required Completion Criteria

### 1. Allocation is dynamic and loop-closed

The system must prove that:

- alpha inputs affect optimizer output
- optimizer output affects weights
- weights affect execution behavior
- execution results affect later allocation or rebalance behavior

### 2. Constraints are enforced system-wide

The system must prove that constraints are not just optimizer math.

They must be:

- applied in allocation
- reflected in execution
- reflected in realized positions
- preserved within tolerance

### 3. Rebalance behavior is real

The system must prove that rebalance is not only one-shot calculation.

It must show:

- allocation can change over time
- position state can move toward new intent
- system reacts to changed inputs, not just static initial weights

### 4. Portfolio intelligence affects outcomes

The system must prove that portfolio decisions are not detached advisory outputs.

They must influence:

- execution plans
- resulting fills
- resulting positions
- resulting equity path

### 5. Closure packet exists

Phase3 is not complete until there is a closure packet equivalent to prior closures:

- proof tests
- verification procedure
- completion memo
- explicit invariants

## Core Invariants To Prove

### Invariant A

```text
alpha changes -> optimizer output changes
```

### Invariant B

```text
optimizer weights -> execution plans change
```

### Invariant C

```text
execution plans -> realized positions move toward allocation intent
```

### Invariant D

```text
portfolio constraints remain respected in resulting positions within tolerance
```

### Invariant E

```text
portfolio decisions produce measurable equity / risk differences
```

### Invariant F

```text
updated results can feed later allocation / rebalance decisions
```

## Deliverables

### A. Proof tests

Suggested file:

- `apps/v12-api/tests/test_phase3_allocation_loop_closure.py`

Initial proof areas:

- optimizer output affects downstream plan set
- changed targets produce changed positions or explicit block reason
- constraints hold in realized or near-realized state
- rebalance path is not static

### B. Verification script

Suggested file:

- `test_bundle/scripts/verify_phase3_allocation_closure.py`

It should inspect:

- allocation inputs
- weights / portfolio outputs
- execution plans
- fills
- realized positions
- resulting equity/risk snapshots

### C. Completion memo

Suggested file:

- `docs/Phase3_allocation_completion_final.md`

## Implementation Work Packages

### Package 1. Define portfolio loop contracts

Files likely involved:

- `apps/v12-api/ai_hedge_bot/portfolio/`
- `apps/v12-api/ai_hedge_bot/api/routes/portfolio.py`
- `apps/v12-api/ai_hedge_bot/api/routes/execution.py`

Work:

- define what counts as allocation intent
- define what counts as realized portfolio effect
- define acceptable tolerance between intent and realized state

### Package 2. Close alpha -> optimizer contract

Goal:

- changed alpha inputs must produce changed optimizer outputs where expected

Work:

- identify stable optimizer input surface
- add tests for changed expected returns / scores -> changed weights

### Package 3. Close optimizer -> execution contract

Goal:

- weights must affect execution plan generation

Work:

- prove that materially different optimizer output changes execution plan set
- prove no silent disconnect between allocation and execution

### Package 4. Close execution -> realized portfolio contract

Goal:

- execution results must move portfolio toward intended allocation

Work:

- compare plan/weight intent against realized positions
- define tolerance bands
- test rebalance movement rather than exact perfection when appropriate

### Package 5. Close constraints end-to-end

Goal:

- constraints must hold beyond optimizer calculation

Work:

- prove gross cap / symbol cap / budget effects remain reflected in resulting positions
- prove execution does not silently violate portfolio constraints

### Package 6. Close result -> reallocation feedback

Goal:

- prove the system can use results to alter later allocation state

Work:

- identify current feedback surfaces
- prove later cycle allocation differs when performance/risk inputs differ
- if not yet implemented, explicitly mark this as the remaining blocker

## Suggested Test Matrix

### Happy path

- alpha input changes
- optimizer weights change
- execution plan changes
- positions move
- equity/risk changes

### Constraint path

- constraints bind
- realized position state still respects constraints within tolerance

### Rebalance path

- prior state exists
- new optimizer intent differs
- realized portfolio moves toward new allocation

### Feedback path

- changed performance/risk inputs
- later allocation differs

### Blocked path

- allocation intent exists
- execution cannot realize it
- explicit reason / degradation is emitted

## Non-Goals For Phase3 Closure

These should not block Phase3 closure unless scope changes:

- large-scale alpha factory automation
- live trading deployment
- full self-improving loop
- all future strategy research

## Exit Condition

Phase3 can be marked complete when:

- completion criteria are documented
- proof tests pass
- verification script passes
- completion memo is written
- architect agrees the allocation loop is closed

## References

- [Phase2_phase3_status_for_architect.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Phase2_phase3_status_for_architect.md)
- [After_Sprint6H_Roadmap_from_Architect.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/After_Sprint6H_Roadmap_from_Architect.md)
- [Phase2_execution_completion_final.md](/C:/work_data/pyWorkSpace/QuantOpsV12/QuantOps_github/docs/Phase2_execution_completion_final.md)

## Working Summary

```text
Phase3 is not blocked by missing optimizer components alone.
Phase3 is blocked by missing proof that allocation intent becomes realized portfolio behavior through a closed loop.
```

## Progress Update

As of `2026-03-29`, the first proof packet is now partially in place:

- score-driven allocation intent is implemented in runtime portfolio preparation
- `apps/v12-api/tests/test_phase3_allocation_loop_closure.py` exists and passes
- `test_bundle/scripts/verify_phase3_allocation_closure.py` exists and passes against the live paper stack

Phase3 should still be treated as `in_progress` until result -> feedback -> reallocation is also proven and a final completion memo is written.
