# AES-03 Portfolio Integration Design

**Project:** QuantOps / ai_hedge_bot  
**Branch:** `codex/post-phase7-hardening`  
**Lane:** Alpha Evaluation / Selection Intelligence v1  
**Packet:** `AES-03 Integration`  
**Date:** `2026-04-25`

## 0. Purpose

`AES-03` は selected alpha ensemble を作る。  
この設計の目的は、その output を `MPI` と `LCC` に安全に接続すること。

## 1. Core Invariant

```text
Portfolio must consume only alpha ensembles that passed AES-01, AES-02, and AES-03,
and LCC must cap capital before any live exposure is created.
```

## 2. System Boundary

```text
ASD:
  generates alpha
AAE:
  manages lifecycle
AES-01:
  evaluates alpha
AES-02:
  validates OOS survival
AES-03:
  selects ensemble and initial weights
MPI:
  portfolio allocation
LCC:
  live capital caps
Execution:
  orders and fills
```

## 3. Integration Flow

```text
AES-03 selected ensemble
    -> Portfolio-ready payload
    -> MPI staging
    -> MPI allocation decision
    -> LCC capital guardrail
    -> Runtime portfolio weights
    -> Execution layer
    -> fills / pnl / risk feedback
```

## 4. Strict Gate Rules

### 4.1 Portfolio consumption gate

```text
AES-01 decision = promote_candidate
AES-02 decision = validation_pass
AES-03 portfolio_ready = true
governance approval = pass
```

### 4.2 LCC capital gate

```text
LCC must apply:
  per-alpha capital cap
  per-ensemble capital cap
  turnover cap
  drawdown cap
  liquidity/capacity cap
```

## 5. AES-03 -> MPI Payload

```json
{
  "source": "AES-03",
  "run_id": "aes3_run_...",
  "ensemble_id": "ens_...",
  "created_at": "2026-04-25T00:00:00Z",
  "portfolio_ready": true,
  "ensemble_score": 0.74,
  "expected_metrics": {
    "expected_return_score": 0.68,
    "expected_risk_score": 0.42,
    "sharpe_score": 0.71,
    "diversification_score": 0.82,
    "stability_score": 0.76,
    "capacity_score": 0.64
  },
  "alphas": [
    {
      "alpha_id": "alpha_001",
      "family": "momentum",
      "initial_weight": 0.18,
      "aes_score": 0.77,
      "validation_score": 0.69,
      "marginal_score": 0.08,
      "capacity_score": 0.63,
      "max_capital_fraction": 0.05,
      "risk_flags": []
    }
  ]
}
```

## 6. MPI Responsibilities

MPI should treat `AES-03` output as input candidate set, not final portfolio truth.

MPI does:

```text
1. receive selected alpha ensemble
2. check cross-strategy budget
3. compare alpha ensemble with existing strategy allocations
4. apply portfolio-level concentration rules
5. generate target allocation proposal
```

MPI must not:

```text
- re-run AES scoring
- bypass AES validation
- promote non-AES alpha
- ignore LCC caps
```

## 7. LCC Responsibilities

LCC is the last safety gate before runtime capital.

LCC does:

```text
1. read MPI allocation proposal
2. read AES-03 capacity metadata
3. apply capital caps
4. apply drawdown / risk / liquidity guardrails
5. approve, reduce, freeze, or block exposure
```

## 8. Staging Table Design

### portfolio_alpha_ensemble_staging

```sql
create table if not exists portfolio_alpha_ensemble_staging (
    staging_id varchar primary key,
    source varchar not null,
    run_id varchar not null,
    ensemble_id varchar not null,
    payload_json varchar not null,
    portfolio_ready boolean not null,
    consumed_by_mpi boolean default false,
    mpi_consumed_at timestamp,
    created_at timestamp not null
);
```

### portfolio_alpha_allocation_proposals

```sql
create table if not exists portfolio_alpha_allocation_proposals (
    proposal_id varchar primary key,
    source_ensemble_id varchar not null,
    mpi_run_id varchar,
    proposed_allocation_json varchar not null,
    proposed_gross_exposure double,
    proposed_net_exposure double,
    status varchar not null,
    created_at timestamp not null
);
```

### lcc_alpha_capital_decisions

```sql
create table if not exists lcc_alpha_capital_decisions (
    decision_id varchar primary key,
    proposal_id varchar not null,
    ensemble_id varchar not null,
    decision varchar not null,
    approved_gross_exposure double,
    approved_net_exposure double,
    reduction_reason varchar,
    blocked_reason varchar,
    created_at timestamp not null
);
```

## 9. API Surface

```text
GET  /system/alpha-ensemble/portfolio-ready/latest
POST /system/alpha-ensemble/stage-for-portfolio
GET  /system/portfolio/alpha-ensemble-staging/latest
POST /system/portfolio/alpha-allocation-proposal/run
GET  /system/portfolio/alpha-allocation-proposal/latest
POST /system/live-capital/alpha-allocation-review
GET  /system/live-capital/alpha-capital-decisions/latest
```

## 10. Definition of Done

```text
AES-03 selected ensemble can be staged for MPI
MPI can consume only portfolio_ready ensemble
LCC applies capital caps before runtime exposure
unvalidated alpha cannot reach Portfolio
integration is idempotent
failures do not alter runtime allocation
APIs expose staging, proposal, and capital decisions
completed lanes are not replayed
```
