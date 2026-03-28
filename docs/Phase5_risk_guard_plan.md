# Phase5 Risk Guard OS Plan

Date: `2026-03-29`
Repo: `QuantOps_github`
Branch: `main`
Status: `in_progress`

## Objective

Start `Phase5: Risk / Guard OS` as the next closure track after:

- `Phase1 Truth Layer = COMPLETE`
- `Phase2 Execution Reality = COMPLETE`
- `Phase3 Portfolio Intelligence = COMPLETE`
- `Phase4 Alpha Factory = COMPLETE`

Phase5 should not be treated as "some risk flags exist".

It should be treated as:

```text
risk sensing, guard decision, execution blocking, and recovery are closed as a system loop
```

## Working Closure Definition

Phase5 is complete only when this loop is explicitly closed:

```text
risk evidence
-> guard evaluation
-> runtime control / kill-switch / halt decision
-> execution block or degrade behavior
-> persisted reason / state / audit evidence
-> explicit recovery or resume rule
-> next-cycle guard reuse
```

## Existing Repo Evidence

The repo already contains meaningful Phase5 components:

- runtime halt / resume control
- kill switch endpoint
- risk-halt propagation into execution state and reasons
- blocked-by-risk execution diagnosis
- strategy drawdown and global risk snapshots
- risk and strategy budget routes
- tests for execution stop and halt propagation

Relevant current references:

- `apps/v12-api/tests/test_sprint6h8_risk_execution_stop.py`
- `apps/v12-api/tests/test_sprint6h9_2_3_risk_halt_propagation.py`
- `apps/v12-api/ai_hedge_bot/execution/state_machine.py`
- `apps/v12-api/ai_hedge_bot/orchestrator/orchestration_service.py`
- `apps/v12-api/ai_hedge_bot/governance/kill_switch.py`
- `apps/v12-api/ai_hedge_bot/api/routes/runtime.py`
- `apps/v12-api/ai_hedge_bot/api/routes/risk.py`
- `apps/v12-api/ai_hedge_bot/api/routes/strategy.py`

## Likely Closure Invariants

### P5-CLOSE-1

```text
risk evidence -> deterministic guard decision -> execution block / degrade state
```

### P5-CLOSE-2

```text
guard decision -> persisted runtime / execution / audit evidence
```

### P5-CLOSE-3

```text
guarded state in cycle N -> next-cycle execution suppression or constrained reuse
until explicit recovery conditions are met
```

### P5-CLOSE-4

```text
recovery evidence -> deterministic resume / unhalt path
```

## Deliverables

### 1. Architect status packet

Suggested file:

- `docs/Phase5_status_for_architect.md`

### 2. First proof test packet

Suggested file:

- `apps/v12-api/tests/test_phase5_risk_guard_closure.py`

### 3. Live verification script

Suggested file:

- `test_bundle/scripts/verify_phase5_risk_guard_closure.py`

### 4. Completion memo

Suggested file:

- `docs/Phase5_risk_guard_completion_final.md`

## Recommended Execution Order

1. inventory existing risk/guard/runtime-control behavior
2. get architect judgment for exact closure definition
3. implement first proof test for guard decision -> execution consequence
4. add verification script
5. close with completion memo after architect re-judgment

## Exit Condition

Phase5 should only move to `COMPLETE` when the repo can show:

- explicit proof tests
- live verification
- architect re-judgment
- final completion memo

for the full guard lifecycle, not only a kill-switch endpoint.
