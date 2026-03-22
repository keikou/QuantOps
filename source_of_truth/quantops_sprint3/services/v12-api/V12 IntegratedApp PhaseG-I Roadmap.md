**V12 IntegratedApp 完成版ロードマップ**を、**フォルダ構成・API・DuckDBテーブル一覧**まで含めて整理します。

前提は次の通りです。
PhaseD までで shadow execution と execution analytics は完成済みで、`shadow_decisions / shadow_orders / shadow_fills / execution_costs / order_state_transitions / execution_quality_snapshots / slippage_reports / latency_snapshots / shadow_pnl_snapshots` が揃っており、次段の execution-aware development の土台があります。 
また V12 統合設計では、全体は **Research系 / Decision系 / Execution系 / Learning-Governance系** に分かれ、`Trading Service / Evaluation Service / Analytics Service / Portfolio Service / Execution Service / Research Factory Service / Autonomous Alpha Service / Global Portfolio Service / Self Improving Service` の分離が推奨されています。 
さらに governance 側は `Experiment Tracker / Dataset Registry / Feature Registry / Validation Registry / Model Registry / Promotion Policy / Alpha Decay Monitor / Rollback Policy` を中核に置く設計です。

---

# 1. 新フェーズ定義

## PhaseG: IntegratedApp Foundation

対象:

* Data Layer
* Signal Layer
* State
* Orchestrator(backtest / paper / shadow)
* Analytics
* Dashboard

役割:

* V12 IntegratedApp の共通基盤を作る
* `data → signal → portfolio → paper/shadow execution → analytics/dashboard` を単一アプリで回す
* backtest / paper / shadow の mode 差し替えを同一 state 契約で扱う

これは V12 の **Research系 + Decision系の基盤統合**に相当します。

## PhaseH: Global Portfolio & Governance

対象:

* Strategy Registry
* Global Capital Allocator
* Global Risk Engine
* Master Portfolio Dashboard
* Alpha Registry
* Experiment Tracking
* Promotion / Demotion
* Drift Monitoring
* Champion / Challenger
* Alpha Factory Dashboard

役割:

* 複数 strategy を束ねる Portfolio OS を作る
* Research Factory と production governance をつなぐ
* strategy 単位・alpha 単位の昇格/降格ルールを導入する

これは旧 PhaseE の `strategy registry / capital allocator / global risk engine / master portfolio dashboard` と、旧 PhaseF の `alpha registry / experiment tracking / promotion/demotion / drift monitoring` を統合した層です。

## PhaseI: Live Promotion & Production Operations

対象:

* Promotion Gate
* Live Readiness
* Rollback Policy
* Orchestrator(live)
* live Analytics
* live Dashboard
* Reconciliation
* Kill Switch
* Operator Controls
* Incident / Audit / Config Versioning

役割:

* shadow/paper から live へ昇格する運用統治層を作る
* 実運用時の安全装置・監視・復旧を整備する
* production 用の command center を完成させる

これは V9.1 の `live model governance / rollback policy / alpha decay monitor / operator review` を実売買アプリに接続する段階です。

---

# 2. 実装順ロードマップ

## PhaseG 実装順

1. Data Layer
2. Signal Layer
3. State
4. Orchestrator(backtest / paper / shadow)
5. Analytics
6. Dashboard

## PhaseH 実装順

1. Strategy Registry
2. Global Capital Allocator
3. Global Risk Engine
4. Master Portfolio Dashboard
5. Alpha Registry
6. Experiment Tracker
7. Promotion / Demotion
8. Drift Monitoring
9. Champion / Challenger
10. Alpha Factory Dashboard

## PhaseI 実装順

1. Promotion Gate
2. Live Readiness Score
3. Rollback / Recovery
4. Orchestrator(live)
5. live Analytics
6. live Dashboard
7. Reconciliation / Kill Switch / Operator Controls

---

# 3. V12 IntegratedApp 推奨フォルダ構成

```text
ai_hedge_bot/
├─ app/
│  ├─ main.py
│  ├─ startup.py
│  ├─ container.py
│  └─ mode_controller.py
│
├─ core/
│  ├─ config.py
│  ├─ settings.py
│  ├─ enums.py
│  ├─ ids.py
│  ├─ clock.py
│  └─ types.py
│
├─ data/
│  ├─ collectors/
│  ├─ normalization/
│  ├─ quality/
│  ├─ replay/
│  ├─ contracts/
│  └─ storage/
│
├─ signal/
│  ├─ features/
│  ├─ regime/
│  ├─ alpha/
│  ├─ metadata/
│  ├─ signal_quality/
│  ├─ evaluation/
│  └─ signal_service.py
│
├─ portfolio/
│  ├─ expected_return/
│  ├─ risk_model/
│  ├─ optimizer/
│  ├─ dedup/
│  ├─ overlap/
│  ├─ diagnostics/
│  └─ portfolio_service.py
│
├─ state/
│  ├─ market_state.py
│  ├─ signal_state.py
│  ├─ portfolio_state.py
│  ├─ order_state.py
│  ├─ position_state.py
│  ├─ account_state.py
│  ├─ pnl_state.py
│  └─ snapshot_service.py
│
├─ orchestrator/
│  ├─ base.py
│  ├─ backtest_orchestrator.py
│  ├─ paper_orchestrator.py
│  ├─ shadow_orchestrator.py
│  ├─ live_orchestrator.py
│  ├─ cycle_runner.py
│  └─ orchestration_service.py
│
├─ execution/
│  ├─ planner/
│  ├─ shadow/
│  ├─ live/
│  ├─ venue_router/
│  ├─ microstructure/
│  ├─ execution_alpha/
│  └─ tca/
│
├─ analytics/
│  ├─ signal_analytics.py
│  ├─ portfolio_analytics.py
│  ├─ execution_analytics.py
│  ├─ strategy_analytics.py
│  ├─ alpha_analytics.py
│  ├─ live_analytics.py
│  └─ analytics_service.py
│
├─ dashboard/
│  ├─ research_dashboard.py
│  ├─ portfolio_dashboard.py
│  ├─ execution_dashboard.py
│  ├─ global_dashboard.py
│  ├─ alpha_factory_dashboard.py
│  └─ live_dashboard.py
│
├─ strategy/
│  ├─ strategy_registry.py
│  ├─ strategy_runtime.py
│  ├─ strategy_allocator.py
│  ├─ capital_allocator.py
│  ├─ risk_budget_engine.py
│  ├─ cross_strategy_netting.py
│  └─ strategy_service.py
│
├─ research_factory/
│  ├─ experiment_tracker.py
│  ├─ dataset_registry.py
│  ├─ feature_registry.py
│  ├─ validation_registry.py
│  ├─ model_registry.py
│  ├─ promotion_policy.py
│  ├─ alpha_decay_monitor.py
│  ├─ live_model_review.py
│  ├─ rollback_policy.py
│  └─ governance_service.py
│
├─ autonomous_alpha/
│  ├─ alpha_registry.py
│  ├─ idea_generator.py
│  ├─ alpha_builder.py
│  ├─ alpha_backtester.py
│  ├─ alpha_evaluator.py
│  ├─ alpha_ranker.py
│  └─ alpha_factory_service.py
│
├─ monitoring/
│  ├─ healthchecks.py
│  ├─ metrics.py
│  ├─ alerts.py
│  ├─ audit.py
│  └─ incidents.py
│
├─ api/
│  ├─ app.py
│  ├─ routes/
│  │  ├─ system.py
│  │  ├─ market.py
│  │  ├─ signals.py
│  │  ├─ portfolio.py
│  │  ├─ orchestrator.py
│  │  ├─ execution.py
│  │  ├─ analytics.py
│  │  ├─ dashboard.py
│  │  ├─ strategy.py
│  │  ├─ research_factory.py
│  │  ├─ alpha.py
│  │  └─ live.py
│  └─ schemas/
│
├─ db/
│  ├─ migrations/
│  │  ├─ phase_g.sql
│  │  ├─ phase_h.sql
│  │  └─ phase_i.sql
│  └─ duckdb/
│
├─ scheduler/
│  ├─ runner.py
│  ├─ rebalance_jobs.py
│  ├─ evaluation_jobs.py
│  ├─ promotion_jobs.py
│  └─ retraining_jobs.py
│
└─ tests/
   ├─ phase_g/
   ├─ phase_h/
   └─ phase_i/
```

この分割は、V12 統合設計の service 依存分離、および V9.1 の governance 分離と整合します。

---

# 4. PhaseG 完成版ロードマップ

## 4.1 Scope

* Data Layer
* Signal Layer
* State
* backtest/paper/shadow Orchestrator
* Analytics
* Dashboard

## 4.2 実装内容

### Data Layer

* market collector
* orderbook collector
* funding / OI / liquidation collector
* normalization
* symbol mapping
* freshness / missing / anomaly checks
* parquet + DuckDB storage
* replay engine

V12 統合図でも `Market Data Collector / Orderbook Collector / Funding/OI/Liquidations / Tick Store / DuckDB Research DB` が最下層です。 

### Signal Layer

* feature pipeline
* regime classifier
* alpha router
* signal quality model
* signal evaluator
* alpha metadata enrichment
* signal expiry / confidence / family tagging

V4.5.3.2 で必要だった `Signal Deduplication / Alpha Family Metadata / Overlap Scoring / Portfolio Diagnostics` をここで信号契約に埋め込みます。 

### State

* market_state
* signal_state
* portfolio_state
* order_state
* position_state
* account_state
* pnl_state
* recovery checkpoints

### Orchestrator(backtest/paper/shadow)

* 共通 cycle contract
* mode switch
* scheduler integration
* run-once / continuous cycle
* state snapshot persistence

PhaseC/PhaseD ではすでに `/runner/run-cycle` と shadow execution cycle があるため、その上に統合 orchestrator を置く構成が自然です。

### Analytics

* signal summary
* portfolio diagnostics
* execution summary
* slippage report
* lifecycle report
* shadow vs paper comparison

PhaseD では `GET /analytics/shadow-summary /execution-quality /slippage-report /order-lifecycle` が既に定義されています。

### Dashboard

* research dashboard
* portfolio dashboard
* execution dashboard
* shadow dashboard

---

# 5. PhaseH 完成版ロードマップ

## 5.1 Scope

* Strategy Registry
* Global Capital Allocator
* Global Risk Engine
* Master Portfolio Dashboard
* Alpha Registry
* Experiment Tracking
* Promotion / Demotion
* Drift Monitoring
* Champion / Challenger
* Alpha Factory Dashboard

## 5.2 実装内容

### Strategy / Global Portfolio

* strategy registry
* strategy runtime metadata
* global capital allocator
* strategy allocator
* cross-strategy netting
* risk budget engine
* strategy performance analytics
* master portfolio dashboard

旧 PhaseE の中核は `strategy registry / global capital allocator / global risk engine / master portfolio dashboard` です。 

### Research Factory / Governance

* experiment tracker
* dataset registry
* feature registry
* validation registry
* model registry
* promotion policy
* alpha decay monitor
* live model review
* rollback policy

これは V9.1 の定義そのものです。 `model_id / experiment_id / dataset_version / feature_version / validation_metrics / state / live_since / last_review_at` を管理し、model state は `candidate / approved / live / shadow / deprecated / rejected / rolled_back` を持ちます。 

### Autonomous Alpha

* alpha registry
* alpha generation
* alpha testing
* alpha evaluation
* alpha ranking
* alpha library
* champion / challenger runs

V11 では `generate_alpha / test_alpha / evaluate_alpha / store_alpha / rank_alpha` と `POST /alpha/generate / POST /alpha/test / GET /alpha/ranking / GET /alpha/library` が中核です。 

### PhaseH Dashboard

* global portfolio dashboard
* alpha factory dashboard
* governance dashboard
* experiment / promotion dashboard

---

# 6. PhaseI 完成版ロードマップ

## 6.1 Scope

* Promotion Gate
* Live Readiness Score
* Rollback / Recovery
* Orchestrator(live)
* live Analytics
* live Dashboard
* Reconciliation
* Kill Switch
* Operator Controls
* Incident / Audit

## 6.2 実装内容

### Promotion Gate

* live promotion evaluator
* deployment approval record
* readiness scoring
* pre-live checklist
* shadow/live comparison gate

### Live Governance

* rollback trigger evaluation
* operator review queue
* capital reduction / shadow fallback
* live model review
* config freeze / release log

V9.1 では live deploy 後の監視指標として `PnL drift / slippage drift / turnover drift / hit rate drift / alpha decay / risk usage` を監視し、結果として `keep / reduce capital / shadow / rollback` を返す設計です。 

### Orchestrator(live)

* live cycle orchestration
* order manager integration
* exchange adapter integration
* account sync
* live risk monitor
* kill switch
* reconciliation

V12 統合設計でも live trading platform は `Order Manager / Exchange Adapter / Account Sync / Risk Monitor / Kill Switch` を持つべきです。 

### live Analytics / Dashboard

* live pnl analytics
* live slippage / TCA
* reconciliation dashboard
* live vs paper / shadow
* operator alerts
* incident audit view

---

# 7. API 一覧

## 7.1 System

* `GET /system/health`
* `GET /system/mode`
* `POST /system/mode/set`
* `GET /system/startup-status`
* `POST /system/reload-config`

## 7.2 Data / Market

* `GET /market/latest`
* `GET /market/orderbook`
* `GET /market/funding`
* `GET /market/oi`
* `GET /market/liquidations`
* `GET /market/data-quality`
* `GET /market/feed-liveness`

## 7.3 Signals

* `POST /signals/run`
* `GET /signals/latest`
* `GET /signals/{signal_id}`
* `GET /signals/evaluations`
* `GET /signals/quality`
* `GET /signals/overlap`
* `GET /signals/family-exposure`

## 7.4 Portfolio

* `POST /portfolio/evaluate`
* `POST /portfolio/optimize`
* `POST /portfolio/rebuild`
* `GET /portfolio/state`
* `GET /portfolio/diagnostics`
* `GET /portfolio/exposures`
* `GET /portfolio/weights`

`POST /portfolio/evaluate /optimize` は V9.2 系の portfolio intelligence API と一致します。 

## 7.5 Orchestrator

* `POST /orchestrator/backtest/run`
* `POST /orchestrator/paper/run-cycle`
* `POST /orchestrator/shadow/run-cycle`
* `POST /orchestrator/live/run-cycle`
* `GET /orchestrator/status`
* `GET /orchestrator/cycles`
* `POST /orchestrator/stop`

## 7.6 Execution

* `POST /execution/plan`
* `POST /execution/route`
* `POST /execution/submit`
* `GET /execution/status`
* `GET /execution/shadow-orders`
* `GET /execution/shadow-fills`
* `GET /execution/latency`
* `GET /execution/tca`

PhaseD 実装済み API との整合を保っています。

## 7.7 Analytics

* `GET /analytics/signal-summary`
* `GET /analytics/portfolio-summary`
* `GET /analytics/shadow-summary`
* `GET /analytics/execution-quality`
* `GET /analytics/slippage-report`
* `GET /analytics/order-lifecycle`
* `GET /analytics/strategy-summary`
* `GET /analytics/alpha-summary`
* `GET /analytics/live-summary`
* `GET /analytics/live-vs-paper`
* `GET /analytics/live-vs-shadow`

## 7.8 Dashboard

* `GET /dashboard/research`
* `GET /dashboard/portfolio`
* `GET /dashboard/execution`
* `GET /dashboard/global`
* `GET /dashboard/alpha-factory`
* `GET /dashboard/live`

## 7.9 Strategy / PhaseH

* `GET /strategy/registry`
* `POST /strategy/register`
* `POST /strategy/allocate-capital`
* `GET /strategy/risk-budget`
* `GET /strategy/performance`
* `GET /strategy/cross-netting`

## 7.10 Research Factory / PhaseH

* `POST /research-factory/experiments/register`
* `POST /research-factory/datasets/register`
* `POST /research-factory/features/register`
* `POST /research-factory/models/register`
* `POST /research-factory/promotion/evaluate`
* `GET /research-factory/live-review`
* `GET /research-factory/alpha-decay`
* `POST /research-factory/rollback/evaluate`

これらは V9.1 の controller API と一致します。 

## 7.11 Alpha / PhaseH

* `POST /alpha/generate`
* `POST /alpha/test`
* `POST /alpha/evaluate`
* `GET /alpha/ranking`
* `GET /alpha/library`
* `GET /alpha/registry`

V11 API を統合アプリに吸収した形です。 

## 7.12 Live / PhaseI

* `POST /live/promote`
* `POST /live/demote`
* `POST /live/rollback`
* `GET /live/readiness`
* `GET /live/reconciliation`
* `GET /live/risk`
* `POST /live/kill-switch`
* `POST /live/recover`
* `GET /live/incidents`
* `POST /live/operator-action`

---

# 8. DuckDB テーブル一覧

## 8.1 PhaseG: Data Layer

* `market_klines`
* `market_orderbook_snapshots`
* `market_trades`
* `market_funding`
* `market_oi`
* `market_liquidations`
* `market_data_quality_events`
* `market_feed_liveness`
* `dataset_versions`

## 8.2 PhaseG: Signal Layer

* `signals`
* `signal_features`
* `signal_metadata`
* `signal_quality`
* `signal_evaluations`
* `signal_forward_returns`
* `signal_mfe_mae`
* `signal_target_stop_eval`
* `signal_regime_snapshots`

## 8.3 PhaseG: Portfolio 前処理 / Diagnostics

* `portfolio_signal_decisions`
* `portfolio_diagnostics`

これは V4.5.3.2 の必須 analytics テーブルです。 

## 8.4 PhaseG: State

* `state_market_snapshots`
* `state_signal_snapshots`
* `state_portfolio_snapshots`
* `state_order_snapshots`
* `state_position_snapshots`
* `state_account_snapshots`
* `state_pnl_snapshots`
* `state_recovery_checkpoints`

## 8.5 PhaseG: Orchestrator(backtest/paper/shadow)

* `orchestrator_runs`
* `orchestrator_cycles`
* `backtest_runs`
* `backtest_results`
* `paper_orders`
* `paper_fills`
* `paper_positions`
* `paper_pnl_snapshots`
* `shadow_decisions`
* `shadow_orders`
* `shadow_fills`
* `execution_costs`
* `order_events`
* `order_state_transitions`
* `execution_quality_snapshots`
* `slippage_reports`
* `latency_snapshots`
* `shadow_pnl_snapshots`

この shadow 系は PhaseD 完了物をそのまま継承します。 

## 8.6 PhaseG: Analytics

* `analytics_signal_summary`
* `analytics_portfolio_summary`
* `analytics_execution_summary`
* `analytics_shadow_summary`
* `analytics_mode_comparison`

## 8.7 PhaseH: Strategy / Global Portfolio

* `strategy_registry`
* `strategy_runtime_state`
* `strategy_allocations`
* `strategy_risk_budgets`
* `strategy_performance_daily`
* `strategy_drawdown_events`
* `global_capital_allocations`
* `global_risk_snapshots`
* `cross_strategy_correlations`
* `cross_strategy_netting_logs`

## 8.8 PhaseH: Research Factory / Governance

* `experiment_tracker`
* `dataset_registry`
* `feature_registry`
* `validation_registry`
* `model_registry`
* `model_live_reviews`
* `promotion_evaluations`
* `rollback_events`
* `alpha_drift_events`

V9.1 の registry 群に直接対応しています。

## 8.9 PhaseH: Alpha Factory

* `alpha_registry`
* `alpha_experiments`
* `alpha_eval_results`
* `alpha_status_events`
* `alpha_promotions`
* `alpha_demotions`
* `champion_challenger_runs`
* `alpha_rankings`
* `alpha_library`

## 8.10 PhaseI: Live Operations

* `live_orders`
* `live_fills`
* `live_positions`
* `live_account_balances`
* `live_margin_snapshots`
* `live_reconciliation_events`
* `live_risk_events`
* `live_kill_switch_events`
* `live_incidents`
* `live_operator_actions`
* `live_readiness_reviews`
* `live_release_log`
* `live_config_versions`

---

# 9. Phase別の完成定義

## PhaseG 完了条件

* Data → Signal → Portfolio → paper/shadow が単一 orchestrator で回る
* state snapshot / restore が可能
* analytics API が安定
* research / portfolio / execution dashboard が表示可能

## PhaseH 完了条件

* strategy registry と global allocation が稼働
* experiment / dataset / feature / model registry が閉じる
* promotion / demotion / decay monitor が自動判定可能
* alpha factory dashboard が稼働

## PhaseI 完了条件

* live promotion gate が機能
* rollback / shadow fallback / capital reduction が運用可能
* live orchestrator が order manager / exchange adapter / risk monitor と接続
* live analytics / dashboard / reconciliation / kill-switch が機能

---

# 10. 実装優先順位

開発効率だけで見ると、次の順が最も安全です。

**PhaseG**

1. `data/`
2. `signal/`
3. `state/`
4. `orchestrator/backtest_orchestrator.py`
5. `orchestrator/paper_orchestrator.py`
6. `orchestrator/shadow_orchestrator.py`
7. `analytics/`
8. `dashboard/`

**PhaseH**

1. `strategy/strategy_registry.py`
2. `strategy/capital_allocator.py`
3. `strategy/risk_budget_engine.py`
4. `research_factory/experiment_tracker.py`
5. `research_factory/model_registry.py`
6. `research_factory/promotion_policy.py`
7. `research_factory/alpha_decay_monitor.py`
8. `autonomous_alpha/alpha_registry.py`
9. `autonomous_alpha/alpha_evaluator.py`
10. `dashboard/global_dashboard.py`
11. `dashboard/alpha_factory_dashboard.py`

**PhaseI**

1. `research_factory/rollback_policy.py`
2. `orchestrator/live_orchestrator.py`
3. `execution/live/`
4. `monitoring/incidents.py`
5. `analytics/live_analytics.py`
6. `dashboard/live_dashboard.py`

---

# 11. 結論

新命名に全面リネームすると、V12 IntegratedApp は次の3段で固定できます。

* **PhaseG = IntegratedApp Foundation**
  Data / Signal / State / Orchestrator(backtest-paper-shadow) / Analytics / Dashboard

* **PhaseH = Global Portfolio & Governance**
  Strategy Registry / Global Allocation / Global Risk / Research Factory / Alpha Factory / Promotion-Demotion / Drift Monitoring

* **PhaseI = Live Promotion & Production Operations**
  Promotion Gate / Readiness / Rollback / Live Orchestrator / live Analytics / live Dashboard / Reconciliation / Kill Switch

この切り方は、PhaseD の handoff、V12 統合 service 分離、V9.1 governance、V11 alpha factory を一番無理なく接続できます。

次はこれをそのまま **「PhaseG 実装チケット一覧.md」→「PhaseH 実装チケット一覧.md」→「PhaseI 実装チケット一覧.md」** に分解するのが自然です。
