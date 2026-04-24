# AES-03 Weight Optimization Algorithms

**Project:** QuantOps / ai_hedge_bot  
**Branch:** `codex/post-phase7-hardening`  
**Lane:** Alpha Evaluation / Selection Intelligence v1  
**Packet:** `AES-03 Algorithm Design`  
**Date:** `2026-04-25`

## 0. Purpose

`AES-03` は selected alpha ensemble に初期 weight を割り当てる。
目的は raw backtest Sharpe 最大化ではなく、頑健で保守的な weight を作ること。

```text
Weight optimization must be robust, constrained, and conservative.
Do not optimize raw backtest Sharpe aggressively.
```

## 1. Core Invariant

```text
Weights must improve ensemble robustness without concentrating risk into fragile alpha.
```

## 2. Inputs

```text
alpha_id
expected_return_score
volatility
sharpe_score
robustness_score
decay_score
overfit_risk_score
capacity_score
turnover
correlation vector
validation_score
marginal_score
```

## 3. Output

```text
raw_weight
normalized_weight
risk_adjusted_weight
capacity_adjusted_weight
final_weight
weight_reason
```

Constraints:

```text
sum(final_weight) = 1
0 <= final_weight <= max_weight_per_alpha
```

## 4. Candidate Algorithms

```text
1. Equal Weight baseline
2. Score-Proportional Weight
3. Inverse Volatility Weight
4. Correlation-Adjusted Weight
5. Capacity-Capped Weight
6. Robust Hybrid Weight
```

## 5. Algorithm 1: Equal Weight Baseline

```text
w_i = 1 / N
```

Use:

```text
- baseline
- low-confidence fallback
- when covariance is not trustworthy
```

## 6. Algorithm 2: Score-Proportional Weight

```text
raw_i = max(score_i, 0)
w_i = raw_i / sum(raw)
```

Suggested score:

```text
score_i =
    0.35 * aes_score
  + 0.25 * validation_score
  + 0.20 * robustness_score
  + 0.20 * marginal_score
```

## 7. Algorithm 3: Inverse Volatility Weight

```text
raw_i = 1 / (vol_i + epsilon)
w_i = raw_i / sum(raw)
```

## 8. Algorithm 4: Correlation-Adjusted Weight

```text
avg_corr_i = mean(abs(corr(i, j))) for j != i
corr_penalty_i = 1 - clamp(avg_corr_i, 0, 1)
raw_i = base_score_i * corr_penalty_i
w_i = raw_i / sum(raw)
```

Hard rule:

```text
if max_corr_i >= 0.92:
    alpha should not be included
```

## 9. Algorithm 5: Capacity-Capped Weight

```text
cap_i = max_capital_fraction_i / sum(max_capital_fraction)
w_i = min(base_weight_i, cap_i)
renormalize remaining weight across uncapped alphas
```

## 10. Algorithm 6: Robust Hybrid Weight

### Step 1: quality score

```text
quality_i =
    0.30 * aes_score_i
  + 0.25 * validation_score_i
  + 0.20 * robustness_score_i
  + 0.15 * marginal_score_i
  + 0.10 * decay_score_i
```

### Step 2: risk adjustment

```text
risk_adj_i = 1 / (vol_i + epsilon)
```

### Step 3: correlation penalty

```text
corr_adj_i = 1 - clamp(avg_abs_corr_i, 0, 0.9)
```

### Step 4: overfit penalty

```text
overfit_adj_i = 1 - clamp(overfit_risk_i, 0, 1)
```

### Step 5: capacity adjustment

```text
capacity_adj_i = clamp(capacity_score_i, 0, 1)
```

### Step 6: raw weight

```text
raw_i =
    quality_i
  * sqrt(risk_adj_i)
  * corr_adj_i
  * overfit_adj_i
  * capacity_adj_i
```

### Step 7: normalize

```text
w_i = raw_i / sum(raw)
```

### Step 8: caps

```text
w_i = min(w_i, max_weight_per_alpha)
w_i = min(w_i, capacity_cap_i)
renormalize
```

## 11. Recommended Defaults

```yaml
aes03_weights:
  method: robust_hybrid
  max_weight_per_alpha: 0.25
  min_weight_to_keep: 0.03

  fallback:
    if_missing_volatility: use_median_volatility
    if_missing_capacity: 0.05
    if_all_raw_zero: equal_weight

  quality_weights:
    aes_score: 0.30
    validation_score: 0.25
    robustness_score: 0.20
    marginal_score: 0.15
    decay_score: 0.10

  penalties:
    max_corr_hard_reject: 0.92
    avg_corr_penalty_cap: 0.90
    overfit_cap: 1.00

  caps:
    per_alpha_max: 0.25
    per_family_max: 0.40
    per_regime_max: 0.50
```

## 12. Pruning Rule

```text
if final_weight < min_weight_to_keep:
    remove alpha from ensemble
    renormalize
```

## 13. Family Constraint

```text
sum(weights for same family) <= per_family_max
```

## 14. Regime Constraint

```text
sum(weights dependent on same regime) <= per_regime_max
```

## 15. Turnover Control

```text
new_weight =
    lambda * target_weight
  + (1 - lambda) * current_weight
```

Defaults:

```text
lambda = 0.35
max_turnover_per_rebalance = 0.25
```

## 16. Why Not Pure Mean-Variance Optimization First?

```text
mu estimation unstable
covariance unstable with short history
small errors cause large weight changes
turnover rises too much
```

## 17. Optional Advanced Algorithm: Shrinkage Mean-Variance

```text
mu_shrunk = alpha * mu_sample + (1-alpha) * mu_prior
Sigma_shrunk = beta * Sigma_sample + (1-beta) * diag(Sigma)
```

This is not required for the initial `AES-03` checkpoint.

## 18. Acceptance Criteria

```text
weights sum to 1
no weight is negative
no alpha exceeds max_weight_per_alpha
high correlation alpha receives lower weight
high overfit alpha receives lower weight
low capacity alpha receives lower weight
family cap is enforced
small useless weights are pruned
equal weight fallback exists
no NaN / inf weights are produced
```
