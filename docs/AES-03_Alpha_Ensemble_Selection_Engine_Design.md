# AES-03 Alpha Ensemble Selection Engine

**Project:** QuantOps / ai_hedge_bot  
**Branch:** `codex/post-phase7-hardening`  
**Lane:** Alpha Evaluation / Selection Intelligence v1  
**Packet:** `AES-03`  
**Date:** `2026-04-25`

## 0. Purpose

`AES-03` の目的は、個別で評価済みの alpha をそのまま使うのではなく、
組み合わせて強く、相関が弱く、より頑健な alpha の集合を選ぶこと。

## 1. Core Invariant

```text
The system must select alpha combinations that maximize portfolio robustness,
not individual alpha scores.
```

## 2. Inputs

```text
validated_alpha_pool (AES-02 pass)
alpha_scores (AES-01)
correlation_matrix
decay / overfit / robustness metrics
capacity estimates
```

## 3. Outputs

```text
selected_alpha_set
ensemble_weights
expected_portfolio_metrics
selection_reason
```

## 4. System Flow

```text
validated alphas
    -> correlation filter
    -> candidate ensemble generation
    -> marginal contribution calculation
    -> ensemble scoring
    -> selection
```

## 5. Key Components

### 5.1 Correlation Matrix

```text
corr(i, j) = correlation(return_i, return_j)
```

Constraint:

```text
corr < 0.8 for inclusion
hard reject if > 0.92
```

### 5.2 Marginal Contribution

```text
MC_i = PortfolioSharpe(all) - PortfolioSharpe(without i)
```

### 5.3 Ensemble Score

```text
Score = w1 * Sharpe
      + w2 * Diversification
      + w3 * Stability
      + w4 * Capacity
```

Weights:

```text
w1 = 0.4
w2 = 0.25
w3 = 0.2
w4 = 0.15
```

## 6. Selection Algorithm

### Step 1: Seed

```text
top 5 alphas by AES score
```

### Step 2: Greedy Add

```text
for each candidate:
    add alpha if:
        improves portfolio score
        correlation constraints satisfied
```

### Step 3: Prune

```text
remove alpha if marginal contribution < threshold
```

## 7. Constraints

```text
max_alpha_count = 10
max_per_family = 2
min_diversification_score = 0.6
```

## 8. API

```text
GET /system/alpha-ensemble/latest
POST /system/alpha-ensemble/run
```

## 9. Data Model

### alpha_ensemble_runs

```sql
create table alpha_ensemble_runs (
    run_id varchar,
    created_at timestamp,
    alpha_count integer,
    portfolio_score double
);
```

## 10. Definition of Done

```text
validated alpha pool consumed
correlation enforced
ensemble generated
weights assigned
API exposed
portfolio-ready output produced
```

## 11. Non-Goals

```text
- alpha generation
- alpha evaluation
- execution optimization
```

## 12. Next Steps

```text
AES-04 Factor Attribution
AES-05 Capacity & Crowding Risk
```
