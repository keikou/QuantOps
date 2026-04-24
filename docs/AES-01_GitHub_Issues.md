# AES-01 GitHub Issue 完全分解

**Project:** QuantOps / ai_hedge_bot  
**Branch:** `codex/post-phase7-hardening`  
**Lane:** Alpha Evaluation / Selection Intelligence v1  
**Packet:** `AES-01: Robust Alpha Evaluation Engine`  
**Status:** `draft_backlog`

## 0. 背景

`AAE v1` = Alpha Generation Lifecycle Orchestration（complete）  
`ASD v1` = Symbolic / Structural Alpha Generator（core v1）

現状:

```text
✔ 作れる（ASD）
✔ 管理できる（AAE）
✖ 見極めが弱い（ここがボトルネック）
```

## 1. Core Invariant

```text
The system must reliably distinguish real alpha from noise.
```

## 2. AES-01 Goal

```text
1. forward return
2. cost-adjusted performance
3. decay detection
4. robustness
5. overfitting detection
6. redundancy filtering
7. selection decision
```

## 3. Decision Output

```text
promote_candidate
watchlist
needs_more_data
reject_noise
reject_overfit
reject_redundant
reject_decayed
```

## 4. Canonical API

```text
GET  /system/alpha-evaluation/latest
GET  /system/alpha-decay-analysis/latest
GET  /system/alpha-correlation-matrix/latest
GET  /system/alpha-robustness-ranking/latest
GET  /system/alpha-selection-decisions/latest
POST /system/alpha-evaluation/run
GET  /system/alpha-evaluation/candidate/{alpha_id}
```

## 5. Directory Structure

```text
ai_hedge_bot/
  alpha_evaluation/
    candidate_loader.py
    forward_return_engine.py
    cost_adjuster.py
    decay_detector.py
    robustness_engine.py
    overfit_detector.py
    correlation_filter.py
    selection_engine.py
    evaluation_service.py
    schemas.py
```

## 6. DuckDB Tables

### alpha_evaluation_runs

```sql
create table if not exists alpha_evaluation_runs (
    run_id varchar primary key,
    started_at timestamp,
    completed_at timestamp,
    candidate_count integer,
    evaluated_count integer,
    promoted_count integer,
    rejected_count integer,
    status varchar
);
```

### alpha_forward_returns

```sql
create table if not exists alpha_forward_returns (
    run_id varchar,
    alpha_id varchar,
    horizon varchar,
    raw_forward_return double,
    cost_adjusted_return double,
    created_at timestamp
);
```

### alpha_evaluation_scores

```sql
create table if not exists alpha_evaluation_scores (
    run_id varchar,
    alpha_id varchar,
    mean_return double,
    hit_rate double,
    sharpe_like double,
    turnover double,
    cost_penalty double,
    decay_score double,
    robustness_score double,
    overfit_risk double,
    redundancy_score double,
    final_score double,
    decision varchar
);
```

## 7. GitHub Issues

### AES-001 — Schema

**Title**  
Add AES-01 evaluation schema

**Tasks**

- evaluation tables 作成
- migration追加
- idempotent保証

### AES-002 — Candidate Loader

**Title**  
Load candidates from AAE / ASD

**Tasks**

- `load_latest_candidates()`
- schema統一

### AES-003 — Forward Return Engine

**Title**  
Compute forward returns

**Tasks**

- horizon対応
- long/short符号処理

### AES-004 — Cost Adjuster

**Title**  
Apply cost penalties

**Tasks**

- fee
- slippage
- turnover

### AES-005 — Score Aggregator

**Title**  
Aggregate alpha scores

**Tasks**

- mean / hit_rate / sharpe
- sample_count管理

### AES-006 — Decay Detector

**Title**  
Detect alpha decay

### AES-007 — Robustness Engine

**Title**  
Evaluate stability

### AES-008 — Overfit Detector

**Title**  
Detect overfitting

### AES-009 — Correlation Filter

**Title**  
Remove redundant alpha

### AES-010 — Selection Engine

**Title**  
Generate decisions

**Rules**

```text
if score high and stable → promote
if weak → reject_noise
if overfit → reject_overfit
if redundant → reject_redundant
if decay → reject_decayed
```

### AES-011 — Evaluation Orchestrator

**Title**  
Run full evaluation pipeline

### AES-012 — API

**Title**  
Expose evaluation endpoints

### AES-013 — Tests

**Title**  
Add unit + contract tests

### AES-014 — AAE Bridge

**Title**  
Send promoted alpha to AAE

## 8. Execution Order

```text
Core:
001 → 002 → 003 → 004 → 005 → 010 → 011 → 012

Quality:
006 → 007 → 008 → 009

Integration:
013 → 014
```

## 9. Definition of Done

```text
✔ candidate load
✔ forward return
✔ cost-adjusted return
✔ scoring
✔ decay detection
✔ overfit detection
✔ redundancy filtering
✔ selection decision
✔ API exposure
✔ downstream連携
```

## 10. Non-Goals

```text
✖ alpha生成（ASDの責務）
✖ execution改善
✖ portfolio最適化
✖ completed lane の再実装
```

## 11. Next Packets

```text
AES-02 Walk-Forward Validation
AES-03 Ensemble Selection
AES-04 Factor Attribution
AES-05 Capacity & Crowding
```
