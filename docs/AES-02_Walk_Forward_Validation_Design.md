# AES-02 Walk-Forward / Out-of-Sample Validation Engine

**Project:** QuantOps / ai_hedge_bot  
**Branch:** `codex/post-phase7-hardening`  
**Lane:** Alpha Evaluation / Selection Intelligence v1  
**Packet:** `AES-02: Walk-Forward / Out-of-Sample Validation Engine`  
**Status:** `draft_v1`  
**Date:** `2026-04-25`

## 0. Purpose

`AES-01` は alpha candidate を評価し、`promote / watchlist / reject` を返す。  
ただし `AES-01` 単体では、将来データでの再現性まで保証しない。

`AES-02` の目的は、alpha candidate を `walk-forward / out-of-sample validation` に通し、採用前の最終生存確認を行うこと。

```text
1. in-sample だけで強い alpha を落とす
2. out-of-sample でも残る alpha を選ぶ
3. regime 変化に耐える alpha を残す
4. promotion 前の最終評価ゲートを置く
```

## 1. Core Invariant

```text
An alpha must survive out-of-sample validation before being treated as production-promotable.
```

## 2. Position in System

```text
ASD
  -> generates alpha structures

AAE
  -> manages alpha lifecycle

AES-01
  -> evaluates performance, cost, decay, overfit, redundancy

AES-02
  -> validates out-of-sample survival

AAE Promotion
  -> promotes only AES-validated alpha

Portfolio
  -> consumes only promoted alpha
```

## 3. High-Level Flow

```text
alpha_candidate
    |
    v
historical data split
    |
    v
walk-forward windows
    |
    v
train / evaluate threshold-free metrics
    |
    v
out-of-sample scoring
    |
    v
stability analysis
    |
    v
validation decision
```

## 4. Canonical API Surface

```text
POST /system/alpha-walk-forward/run
GET  /system/alpha-walk-forward/latest
GET  /system/alpha-walk-forward/candidate/{alpha_id}
GET  /system/alpha-oos-validation/latest
GET  /system/alpha-validation-decisions/latest
GET  /system/alpha-validation-failures/latest
```

## 5. Directory Structure

```text
ai_hedge_bot/
  alpha_validation/
    __init__.py
    window_builder.py
    walk_forward_engine.py
    oos_evaluator.py
    stability_analyzer.py
    validation_decision_engine.py
    validation_service.py
    schemas.py

  api/routes/
    alpha_validation.py

  db/migrations/
    20260425_aes02_alpha_validation.sql

  tests/
    test_aes02_window_builder.py
    test_aes02_walk_forward_engine.py
    test_aes02_oos_evaluator.py
    test_aes02_stability_analyzer.py
    test_aes02_validation_decision_engine.py
    test_aes02_api_contract.py
```

## 6. Data Model

### 6.1 alpha_validation_runs

```sql
create table if not exists alpha_validation_runs (
    run_id varchar primary key,
    started_at timestamp not null,
    completed_at timestamp,
    candidate_count integer,
    validated_count integer,
    passed_count integer,
    failed_count integer,
    status varchar not null,
    notes varchar
);
```

### 6.2 alpha_walk_forward_windows

```sql
create table if not exists alpha_walk_forward_windows (
    run_id varchar not null,
    alpha_id varchar not null,
    window_id varchar not null,
    train_start timestamp not null,
    train_end timestamp not null,
    test_start timestamp not null,
    test_end timestamp not null,
    symbol varchar,
    regime varchar,
    created_at timestamp not null
);
```

### 6.3 alpha_oos_scores

```sql
create table if not exists alpha_oos_scores (
    run_id varchar not null,
    alpha_id varchar not null,
    window_id varchar not null,
    sample_count integer,
    train_score double,
    test_score double,
    train_sharpe double,
    test_sharpe double,
    train_hit_rate double,
    test_hit_rate double,
    score_gap double,
    degradation_ratio double,
    passed boolean,
    fail_reason varchar,
    created_at timestamp not null
);
```

### 6.4 alpha_validation_summary

```sql
create table if not exists alpha_validation_summary (
    run_id varchar not null,
    alpha_id varchar not null,
    total_windows integer,
    passed_windows integer,
    pass_rate double,
    mean_oos_score double,
    median_oos_score double,
    mean_degradation_ratio double,
    worst_window_score double,
    stability_score double,
    final_validation_score double,
    decision varchar not null,
    reason varchar,
    created_at timestamp not null
);
```

## 7. Window Design

### 7.1 Default walk-forward split

```text
train_window = 90 days
test_window = 30 days
step_size = 30 days
min_windows = 4
```

### 7.2 Alternative for high-frequency data

```text
train_window = 20 trading days
test_window = 5 trading days
step_size = 5 trading days
min_windows = 8
```

### 7.3 Window rule

```text
train_end < test_start
no lookahead
no overlap leakage from future labels
```

## 8. OOS Metrics

各 window で最低限次を出す。

```text
train_score
test_score
score_gap
degradation_ratio
test_sharpe
test_hit_rate
test_cost_adjusted_return
```

### 8.1 Score gap

```text
score_gap = train_score - test_score
```

### 8.2 Degradation ratio

```text
degradation_ratio = test_score / (train_score + epsilon)
```

### 8.3 Window pass rule

```text
test_score >= min_oos_score
degradation_ratio >= min_degradation_ratio
test_sharpe >= min_oos_sharpe
test_cost_adjusted_return > 0
```

## 9. Default Thresholds

```yaml
aes02_validation:
  windows:
    min_windows: 4
    min_pass_rate: 0.60

  oos:
    min_oos_score: 0.45
    min_oos_sharpe: 0.25
    min_degradation_ratio: 0.50
    max_score_gap: 0.40

  stability:
    min_stability_score: 0.55

  final:
    promote_validation_min: 0.65
    watchlist_validation_min: 0.45
```

## 10. Validation Decisions

```text
validation_pass
validation_watchlist
validation_fail_oos
validation_fail_unstable
validation_fail_degraded
validation_needs_more_data
```

## 11. Decision Rules

### 11.1 validation_pass

```text
total_windows >= 4
pass_rate >= 0.60
mean_oos_score >= 0.45
mean_degradation_ratio >= 0.50
stability_score >= 0.55
final_validation_score >= 0.65
```

### 11.2 validation_watchlist

```text
total_windows >= 4
pass_rate >= 0.40
mean_oos_score >= 0.35
final_validation_score >= 0.45
```

### 11.3 validation_fail_oos

```text
mean_oos_score < 0.35
or test_cost_adjusted_return <= 0 in majority of windows
```

### 11.4 validation_fail_degraded

```text
mean_degradation_ratio < 0.50
or score_gap > 0.40 in majority of windows
```

### 11.5 validation_fail_unstable

```text
stability_score < 0.55
or worst_window_score is strongly negative
```

### 11.6 validation_needs_more_data

```text
total_windows < 4
or insufficient samples in test windows
```

## 12. Final Validation Score

```text
final_validation_score =
    0.35 * mean_oos_score
  + 0.25 * pass_rate
  + 0.20 * stability_score
  + 0.20 * mean_degradation_ratio
```

All components must be normalized to `[0, 1]`.

## 13. Stability Score

```text
stability_score =
    1 - normalized_std(test_scores)
```

Additional penalties:

```text
single_good_window_dependency
large negative worst window
regime concentration
symbol concentration
```

## 14. Integration with AES-01

`AES-02` should consume `AES-01` outputs.

Input candidates:

```text
AES-01 decision in:
    promote_candidate
    watchlist
```

Recommended rule:

```text
AES-01 promote_candidate
    -> must pass AES-02 before production promotion

AES-01 watchlist
    -> can enter AES-02 if enough data
```

`AES-02` output should update promotion eligibility:

```text
AES-01 promote_candidate + AES-02 validation_pass
    -> production_promotable

AES-01 promote_candidate + AES-02 validation_watchlist
    -> promotion_hold

AES-01 promote_candidate + AES-02 validation_fail
    -> reject or watchlist downgrade
```

## 15. Integration with AAE

AAE remains lifecycle orchestrator.

AAE responsibilities:

```text
submit candidate to AES-01
submit eligible candidate to AES-02
track validation status
promote only validated candidates
archive failed candidates
```

AAE must not compute OOS metrics directly.

## 16. Portfolio Gate

Portfolio must only consume alpha satisfying:

```text
AES-01 decision = promote_candidate
AES-02 decision = validation_pass
governance approval = true
capacity check = pass
```

This prevents direct ASD-generated alpha from entering live allocation.

## 17. GitHub Issue Breakdown

### AES2-001 - Add validation schema and migration

Tasks:

```text
create alpha_validation_runs
create alpha_walk_forward_windows
create alpha_oos_scores
create alpha_validation_summary
add idempotent migration
```

Acceptance:

```text
migration runs repeatedly without failure
existing AES-01 tables remain intact
```

### AES2-002 - Implement Window Builder

Tasks:

```text
build rolling train/test windows
prevent lookahead
support configurable train/test/step
support min window requirement
```

Acceptance:

```text
all windows satisfy train_end < test_start
window count is deterministic
insufficient data returns needs_more_data
```

### AES2-003 - Implement Walk-Forward Engine

Tasks:

```text
run candidate across all windows
compute train and test metrics
persist window results
handle partial failures
```

Acceptance:

```text
each candidate has per-window scores
failed windows do not crash full run
```

### AES2-004 - Implement OOS Evaluator

Tasks:

```text
calculate score_gap
calculate degradation_ratio
calculate OOS pass/fail
store fail_reason
```

Acceptance:

```text
degraded alpha fails
stable OOS alpha passes
```

### AES2-005 - Implement Stability Analyzer

Tasks:

```text
calculate stability across windows
penalize single-window dependency
penalize worst-window collapse
penalize regime concentration
```

Acceptance:

```text
unstable alpha gets lower stability score
consistent alpha gets higher score
```

### AES2-006 - Implement Validation Decision Engine

Tasks:

```text
combine OOS score, pass rate, stability, degradation
emit validation decision
emit reason
```

Acceptance:

```text
pass / watchlist / fail decisions are deterministic
reason is human-readable
```

### AES2-007 - Add Validation API Routes

Tasks:

```text
POST /system/alpha-walk-forward/run
GET  /system/alpha-walk-forward/latest
GET  /system/alpha-walk-forward/candidate/{alpha_id}
GET  /system/alpha-oos-validation/latest
GET  /system/alpha-validation-decisions/latest
```

Acceptance:

```text
endpoints return 200
empty state is safe
latest run_id is included
```

### AES2-008 - Connect AES-02 to AAE Promotion Flow

Tasks:

```text
mark validation_pass as production_promotable
mark validation_watchlist as promotion_hold
mark validation_fail as rejected or downgraded
prevent unvalidated alpha promotion
```

Acceptance:

```text
AAE cannot promote alpha without AES-02 pass
Portfolio sees only validated promoted alpha
```

### AES2-009 - Add Tests

Tests:

```text
test_aes02_window_builder.py
test_aes02_walk_forward_engine.py
test_aes02_oos_evaluator.py
test_aes02_stability_analyzer.py
test_aes02_validation_decision_engine.py
test_aes02_api_contract.py
```

Acceptance:

```text
lookahead prevention test passes
degradation detection test passes
unstable alpha fails
stable alpha passes
API contract stable
```

## 18. Execution Order

```text
Core:
AES2-001
AES2-002
AES2-003
AES2-004
AES2-006
AES2-007

Quality:
AES2-005
AES2-008
AES2-009
```

## 19. Definition of Done

```text
walk-forward windows are generated without lookahead
OOS metrics are computed per window
degradation ratio is computed
stability score is computed
validation decision is emitted
AAE promotion requires AES-02 pass
Portfolio cannot consume unvalidated alpha
API exposes validation state
tests cover windowing, OOS failure, stability and API
```

## 20. Non-Goals

```text
- generating new alpha
- changing AES-01 scoring formulas
- portfolio allocation optimization
- live capital control changes
- completed lane replay
```

## 21. Next Packet Candidates

```text
AES-03: Alpha Ensemble Selection Engine
AES-04: Economic Meaning / Factor Attribution Engine
AES-05: Capacity & Crowding Risk Engine
```
