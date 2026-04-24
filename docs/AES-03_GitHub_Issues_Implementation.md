# AES-03 GitHub Issues Implementation

**Project:** QuantOps / ai_hedge_bot  
**Branch:** `codex/post-phase7-hardening`  
**Lane:** Alpha Evaluation / Selection Intelligence v1  
**Packet:** `AES-03: Alpha Ensemble Selection Engine`  
**Status:** `draft_backlog`  
**Date:** `2026-04-25`

## 0. Background

`AES-01` evaluates alpha quality.  
`AES-02` validates out-of-sample survival.  
`AES-03` selects the portfolio-ready ensemble from the surviving pool.

## 1. Core Invariant

```text
The system must select alpha combinations that improve portfolio-level robustness,
not just individual alpha scores.
```

## 2. AES-03 Goal

```text
1. consume AES-02 validated alpha pool
2. evaluate correlation and family concentration
3. generate ensemble candidates
4. compute marginal contribution
5. score ensembles
6. produce selected alpha set and initial weights
7. emit MPI / LCC portfolio-ready payload
```

## 3. Canonical API Surface

```text
POST /system/alpha-ensemble/run
GET  /system/alpha-ensemble/latest
GET  /system/alpha-ensemble/candidates/latest
GET  /system/alpha-ensemble/candidate/{ensemble_id}
GET  /system/alpha-ensemble-correlation/latest
GET  /system/alpha-marginal-contribution/latest
GET  /system/alpha-ensemble-selection/latest
GET  /system/alpha-ensemble-weights/latest
```

## 4. Directory Structure

```text
ai_hedge_bot/
  alpha_ensemble/
    __init__.py
    validated_alpha_loader.py
    ensemble_candidate_generator.py
    ensemble_correlation_engine.py
    marginal_contribution_engine.py
    diversification_scorer.py
    ensemble_scoring_engine.py
    ensemble_weight_allocator.py
    ensemble_selection_engine.py
    ensemble_service.py
    schemas.py
```

## 5. DuckDB Tables

### alpha_ensemble_runs

```sql
create table if not exists alpha_ensemble_runs (
    run_id varchar primary key,
    started_at timestamp not null,
    completed_at timestamp,
    validated_alpha_count integer,
    candidate_ensemble_count integer,
    selected_alpha_count integer,
    portfolio_score double,
    status varchar not null,
    notes varchar
);
```

### alpha_ensemble_candidates

```sql
create table if not exists alpha_ensemble_candidates (
    run_id varchar not null,
    ensemble_id varchar not null,
    alpha_ids varchar not null,
    alpha_count integer,
    source varchar,
    created_at timestamp not null
);
```

### alpha_ensemble_correlations

```sql
create table if not exists alpha_ensemble_correlations (
    run_id varchar not null,
    alpha_id_a varchar not null,
    alpha_id_b varchar not null,
    correlation double,
    overlap_score double,
    hard_redundant boolean,
    created_at timestamp not null
);
```

### alpha_marginal_contributions

```sql
create table if not exists alpha_marginal_contributions (
    run_id varchar not null,
    ensemble_id varchar not null,
    alpha_id varchar not null,
    contribution_to_return double,
    contribution_to_risk double,
    contribution_to_sharpe double,
    contribution_to_diversification double,
    marginal_score double,
    created_at timestamp not null
);
```

### alpha_ensemble_scores

```sql
create table if not exists alpha_ensemble_scores (
    run_id varchar not null,
    ensemble_id varchar not null,
    alpha_count integer,
    expected_return_score double,
    expected_risk_score double,
    sharpe_score double,
    diversification_score double,
    stability_score double,
    capacity_score double,
    concentration_penalty double,
    final_ensemble_score double,
    decision varchar,
    reject_reason varchar,
    created_at timestamp not null
);
```

### alpha_ensemble_weights

```sql
create table if not exists alpha_ensemble_weights (
    run_id varchar not null,
    ensemble_id varchar not null,
    alpha_id varchar not null,
    raw_weight double,
    normalized_weight double,
    cap_adjusted_weight double,
    final_weight double,
    weight_reason varchar,
    created_at timestamp not null
);
```

### alpha_ensemble_selection

```sql
create table if not exists alpha_ensemble_selection (
    selection_id varchar primary key,
    run_id varchar not null,
    ensemble_id varchar not null,
    selected boolean not null,
    selected_alpha_ids varchar not null,
    portfolio_ready boolean not null,
    reason varchar,
    created_at timestamp not null
);
```

## 6. GitHub Issues

### AES3-001 Add AES-03 database schema and migration
- add all ensemble tables
- make migration idempotent

### AES3-002 Implement Validated Alpha Loader
- load AES-02 `validation_pass`
- join AES-01 score / decay / overfit / robustness

### AES3-003 Implement Ensemble Candidate Generator
- generate candidate sets from validated pool
- enforce `max_alpha_count`
- enforce `max_per_family`

### AES3-004 Implement Ensemble Correlation Engine
- compute pairwise correlation
- compute redundancy flags

### AES3-005 Implement Diversification Scorer
- score family, symbol, regime diversification

### AES3-006 Implement Marginal Contribution Engine
- estimate per-alpha contribution inside ensemble

### AES3-007 Implement Ensemble Scoring Engine
- compute final ensemble score

### AES3-008 Implement Ensemble Weight Allocator
- assign initial weights
- normalize
- cap

### AES3-009 Implement Ensemble Selection Engine
- choose final ensemble
- emit portfolio-ready state

### AES3-010 Implement AES-03 Orchestrator
- build end-to-end run

### AES3-011 Add AES-03 API Routes
- expose canonical endpoints

### AES3-012 Implement Portfolio-Ready Payload Builder
- emit MPI/LCC-compatible payload

### AES3-013 Connect AES-03 Output to MPI Staging
- stage selected ensemble for MPI

### AES3-014 Connect AES-03 Output to LCC Guardrail Metadata
- expose capacity and risk caps

### AES3-015 Add Unit Tests for Candidate Generation and Correlation

### AES3-016 Add Unit Tests for Scoring, Weights and Selection

### AES3-017 Add API Contract Tests

### AES3-018 Add Documentation and Runbook

## 7. Execution Order

```text
P0 Core:
AES3-001
AES3-002
AES3-003
AES3-004
AES3-007
AES3-008
AES3-009
AES3-010
AES3-011
AES3-015
AES3-016
AES3-017

P1 Integration:
AES3-005
AES3-006
AES3-012
AES3-013
AES3-014

P2 Docs:
AES3-018
```

## 8. Definition of Done

```text
AES-02 validated alpha pool loaded
ensemble candidates generated
correlation and redundancy enforced
diversification scored
marginal contribution computed
ensemble score computed
initial weights assigned
portfolio-ready selected ensemble emitted
MPI/LCC payload produced
API usable
tests pass
completed lanes not replayed
```
