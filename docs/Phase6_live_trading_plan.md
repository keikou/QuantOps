# Phase6 Live Trading Plan

Date: `2026-03-29`
Repo: `QuantOps_github`
Branch: `main`
Status: `planning`

## Objective

Start `Phase6: Live Trading` as the next closure track after:

- `Phase1 Truth Layer = COMPLETE`
- `Phase2 Execution Reality = COMPLETE`
- `Phase3 Portfolio Intelligence = COMPLETE`
- `Phase4 Alpha Factory = COMPLETE`
- `Phase5 Risk / Guard OS = COMPLETE`

Phase6 should not be treated as "a live mode flag exists".

It should be treated as:

```text
exchange-connected execution, account synchronization, reconciliation, risk enforcement,
and operator controls are closed as a real-capital system loop
```

## Working Closure Definition

Phase6 is complete only when this loop is explicitly closed:

```text
live intent
-> venue routing / exchange adapter send
-> live order lifecycle
-> live fills / account sync / positions / balances
-> reconciliation against truth
-> live guard / incident / kill-switch response
-> explicit operator recovery / resume control
```

## Existing Repo Evidence

The repo already contains meaningful Phase6-adjacent components:

- live orchestrator scaffold
- live analytics scaffold
- live dashboard scaffold
- venue router
- public market collector and liveness-related config
- paper/shadow/live mode vocabulary in earlier architecture docs
- kill-switch and runtime control already proven in Phase5

Relevant current references:

- `apps/v12-api/ai_hedge_bot/orchestrator/live_orchestrator.py`
- `apps/v12-api/ai_hedge_bot/analytics/live_analytics.py`
- `apps/v12-api/ai_hedge_bot/dashboard/live_dashboard.py`
- `apps/v12-api/ai_hedge_bot/execution/venue_router.py`
- `apps/v12-api/ai_hedge_bot/data/collectors/binance_public_client.py`
- `apps/v12-api/ai_hedge_bot/research_factory/live_model_review.py`
- `apps/v12-api/V12 IntegratedApp PhaseG-I Roadmap.md`
- `apps/v12-api/v_12_file_structure.md`

## Likely Closure Invariants

### P6-CLOSE-1

```text
approved live intent
-> deterministic venue routing decision
-> explicit live-send or explicit live-block reason
```

### P6-CLOSE-2

```text
live order send
-> durable live order lifecycle state
-> exchange acknowledgement / reject / cancel evidence
```

### P6-CLOSE-3

```text
exchange fill / account update
-> local live truth reconciliation
-> balances / positions / margin stay synchronized or incident is raised
```

### P6-CLOSE-4

```text
live breach / venue failure / reconciliation drift
-> deterministic live guard action
-> operator-visible incident and recovery path
```

## Deliverables

### 1. Architect status packet

Suggested file:

- `docs/Phase6_status_for_architect.md`

### 2. First proof test packet

Suggested file:

- `apps/v12-api/tests/test_phase6_live_trading_closure.py`

### 3. Verification script

Suggested file:

- `test_bundle/scripts/verify_phase6_live_trading_closure.py`

### 4. Completion memo

Suggested file:

- `docs/Phase6_live_trading_completion_final.md`

## Architect Initial Verdict

Initial architect judgment:

```text
Phase6 = NOT STARTED AS A CLOSED PHASE
```

Interpretation:

- the repo has live-facing scaffolds and prerequisites
- but there is still no accepted closure packet
- live mode naming or adapter stubs do not count as phase progress by themselves

Architect-confirmed closure framing:

```text
approved live intent
-> deterministic routing / submission decision
-> explicit live send or explicit live block
-> order / fill / account lifecycle
-> reconciliation against venue/account truth
-> guard / incident decision
-> deterministic recovery / rollback / resume
```

Architect-confirmed `Phase6-CLOSE-1` starting point:

```text
approved live intent
-> deterministic venue routing decision
-> explicit live-send or live-block reason
```

Architect-confirmed hardest gap:

```text
live lifecycle + reconciliation closure
```

More exact wording:

```text
first blocker = account/reconciliation truth
```

## Recommended Execution Order

1. get architect judgment for exact closure definition
2. inventory which live-facing components are real versus scaffold-only
3. implement first proof for `live intent -> explicit venue send or block reason`
4. add live order lifecycle persistence proof
5. add reconciliation / account-sync proof
6. add live guard / incident / recovery proof
7. add verification script
8. close with completion memo after architect re-judgment

## Exit Condition

Phase6 should only move to `COMPLETE` when the repo can show:

- explicit proof tests
- live-trading verification procedure or deterministic simulation harness
- architect re-judgment
- final completion memo

for the full live lifecycle, not only mode naming or adapter scaffolding.
