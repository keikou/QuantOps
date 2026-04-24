# AES Threshold Tuning Strategy

**Project:** QuantOps / ai_hedge_bot  
**Branch:** `codex/post-phase7-hardening`  
**Lane:** Alpha Evaluation / Selection Intelligence v1  
**Target Packet:** `AES-01 / AES-02 bridge`  
**Document Status:** `draft_v1`  
**Date:** `2026-04-25`

## 0. Purpose

AES の閾値は、単に alpha を見つけるためではなく、壊れない運用を前提に設計する。

最重要の目的は次の通り。

```text
1. false positive を抑える
2. overfit alpha を通さない
3. redundant alpha を増やさない
4. capacity / cost に弱い alpha を落とす
5. 実運用候補に watchlist を残せる
```

## 1. Core Principle

```text
Do not optimize thresholds for maximum backtest performance.
Optimize thresholds for survival under regime change.
```

## 2. Decision Classes

```text
promote_candidate
watchlist
needs_more_data
reject_noise
reject_overfit
reject_redundant
reject_decayed
```

## 3. Required Metrics

各 alpha candidate について最低限次を持つ。

```text
sample_count
mean_forward_return
median_forward_return
hit_rate
sharpe_final
robustness_score
decay_score
overfit_risk_score
redundancy_score
cost_penalty
turnover
capacity_proxy
final_score
```

## 4. Safety-First Default Thresholds

### 4.1 sample_count

```text
min_sample_count_promote = 250
min_sample_count_watchlist = 80
```

判定:

```text
sample_count < 80
    -> needs_more_data

80 <= sample_count < 250
    -> max decision = watchlist
```

### 4.2 Sharpe threshold

```text
min_sharpe_promote = 0.75
min_sharpe_watchlist = 0.35
```

### 4.3 Hit rate threshold

```text
min_hit_rate_promote = 0.53
min_hit_rate_watchlist = 0.50
```

補足:

```text
hit_rate は単独で使わない
payoff ratio と cost-adjusted return を必ず併用する
```

### 4.4 Mean / median return consistency

```text
median_return_must_be_positive = true
mean_median_gap_max = 2.5
```

ルール:

```text
mean positive but median <= 0
    -> reject_noise or watchlist

mean >> median
    -> outlier dependent alpha
    -> downgrade
```

### 4.5 Decay threshold

```text
decay_score_min_promote = 0.80
decay_score_min_watchlist = 0.55
```

判定:

```text
decay_score < 0.55
    -> reject_decayed

0.55 <= decay_score < 0.80
    -> max decision = watchlist
```

### 4.6 Overfit threshold

```text
overfit_risk_max_promote = 0.60
overfit_risk_max_watchlist = 0.85
```

判定:

```text
overfit_risk_score > 0.85
    -> reject_overfit

0.60 < overfit_risk_score <= 0.85
    -> max decision = watchlist
```

### 4.7 Redundancy threshold

```text
redundancy_score_max_promote = 0.70
correlation_max_promote = 0.80
correlation_hard_reject = 0.92
```

判定:

```text
correlation >= 0.92
    -> reject_redundant

0.80 <= correlation < 0.92
    -> only keep if materially better than incumbent
```

### 4.8 Cost / turnover threshold

```text
cost_penalty_max_promote = 0.35
turnover_max_promote = configurable_by_asset_class
```

判定:

```text
cost_adjusted_return <= 0
    -> reject_noise

raw_return positive but cost_adjusted_return negative
    -> reject_noise
```

## 5. Composite Score

```text
final_score =
    0.35 * sharpe_score
  + 0.20 * robustness_score
  + 0.15 * decay_score
  + 0.20 * (1 - overfit_risk_score)
  + 0.10 * (1 - redundancy_score)
```

## 6. Decision Rules

### 6.1 promote_candidate

```text
sample_count >= 250
sharpe_final >= 0.75
hit_rate >= 0.53
median_forward_return > 0
decay_score >= 0.80
overfit_risk_score <= 0.60
redundancy_score <= 0.70
cost_adjusted_return > 0
final_score >= 0.70
```

### 6.2 watchlist

```text
sample_count >= 80
sharpe_final >= 0.35
median_forward_return >= 0
decay_score >= 0.55
overfit_risk_score <= 0.85
final_score >= 0.45
```

### 6.3 needs_more_data

```text
sample_count < 80
or missing forward returns
or insufficient symbol / regime coverage
```

### 6.4 reject_noise

```text
cost_adjusted_return <= 0
or sharpe_final < 0.35
or hit_rate < 0.50
or final_score < 0.45
```

### 6.5 reject_overfit

```text
overfit_risk_score > 0.85
or complexity too high with low sample count
or in_sample_out_sample_gap too large
```

### 6.6 reject_redundant

```text
correlation >= 0.92 with existing promoted alpha
or redundancy_score > 0.85
```

### 6.7 reject_decayed

```text
decay_score < 0.55
or recent_window_score <= 0 while early_window_score was positive
```

## 7. Threshold Tuning Process

### Step 1: Start conservative

```text
promote threshold high
watchlist threshold moderate
reject threshold explicit
```

### Step 2: Calibrate on historical candidates

候補を最低限次に分ける。

```text
known_good
known_bad
unknown
```

見るもの:

```text
false positive rate
false negative rate
promotion rate
watchlist conversion rate
decay after promotion
cost-adjusted degradation
```

### Step 3: Use rolling calibration

```text
rolling_window = 3 to 6 months
do not tune daily
```

### Step 4: Never optimize one metric alone

避ける:

```text
maximize Sharpe only
maximize hit rate only
maximize final_score only
```

使う:

```text
Sharpe + robustness + decay + overfit + cost + redundancy
```

### Step 5: Promotion budget

```text
max_promotions_per_run = 3
max_promotions_per_family = 1
```

## 8. Regime-Aware Thresholding

### Stable regime

```text
promote_final_score_min = 0.70
decay_min = 0.80
```

### Volatile regime

```text
promote_final_score_min = 0.78
robustness_min = 0.70
cost_penalty_max = 0.25
```

### Low liquidity regime

```text
turnover threshold stricter
slippage penalty higher
capacity requirement stricter
```

## 9. Asset-Class Overrides

### Equities

```text
min_sample_count_promote = 250
correlation_max_promote = 0.80
```

### Crypto

```text
min_sample_count_promote = 500
decay_score_min_promote = 0.85
cost_penalty_max_promote = 0.25
```

### FX / Futures

```text
turnover tolerance can be higher
but slippage model must be venue-aware
```

## 10. Guardrails

### Hard veto rules

```text
overfit_risk_score > 0.85
decay_score < 0.55
cost_adjusted_return <= 0
correlation >= 0.92 with active alpha
sample_count < 80
```

### Soft downgrade rules

```text
sample_count < 250
single-symbol dependency
single-regime dependency
mean positive but median non-positive
high turnover
unstable horizon performance
```

## 11. Monitoring After Promotion

```text
live hit rate
live cost-adjusted return
realized slippage
drawdown contribution
correlation drift
decay acceleration
```

自動 downgrade 条件:

```text
live_decay_score < 0.55
realized_cost > expected_cost * 1.5
live_sharpe drops below 0.25
correlation with existing alpha rises above 0.92
```

## 12. Recommended Config Object

```yaml
aes_thresholds:
  sample_count:
    watchlist_min: 80
    promote_min: 250

  sharpe:
    watchlist_min: 0.35
    promote_min: 0.75

  hit_rate:
    watchlist_min: 0.50
    promote_min: 0.53

  decay:
    watchlist_min: 0.55
    promote_min: 0.80
    hard_reject_below: 0.55

  overfit:
    promote_max: 0.60
    watchlist_max: 0.85
    hard_reject_above: 0.85

  redundancy:
    promote_max: 0.70
    correlation_promote_max: 0.80
    correlation_hard_reject: 0.92

  score:
    watchlist_min: 0.45
    promote_min: 0.70

  promotion_budget:
    max_promotions_per_run: 3
    max_promotions_per_family: 1
```

## 13. Definition of Done

```text
thresholds are config-driven
hard veto rules exist
watchlist path exists
promotion budget exists
asset-class overrides exist
regime-aware overrides exist
threshold changes are logged
no completed lane replay is required
```

## 14. Non-Goals

```text
- daily auto-optimization of thresholds
- maximizing backtest Sharpe
- replacing AES-02 walk-forward validation
- changing ASD generation logic
- changing portfolio allocation logic
```
