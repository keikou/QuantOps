# V12 file structure

## 1. 目的

本書は **V12 IntegratedApp / Self-Improving Quant System** の実装着手用に、
以下を一体で定義する。

- 開発用フォルダ構成
- ファイル名一覧
- DuckDBテーブル定義

対象スコープは **PhaseA〜H**。

---

# 2. ルート構成

```text
ai_hedge_bot/
├─ README.md
├─ requirements.txt
├─ docker-compose.yml
├─ Dockerfile
├─ .env.example
├─ pyproject.toml
├─ pytest.ini
│
├─ docs/
│  ├─ V12_Full_System_Architecture_PhaseA-H.md
│  ├─ PhaseH_Completion_Report.md
│  ├─ V12_System_Architecture_Diagram_Complete.md
│  └─ V12_file_structure.md
│
├─ app/
│  ├─ main.py
│  ├─ startup.py
│  ├─ shutdown.py
│  ├─ container.py
│  └─ mode_controller.py
│
├─ core/
│  ├─ config.py
│  ├─ settings.py
│  ├─ enums.py
│  ├─ ids.py
│  ├─ clock.py
│  ├─ logging.py
│  ├─ exceptions.py
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
├─ risk/
│  ├─ pretrade.py
│  ├─ realtime_risk.py
│  ├─ drawdown_guard.py
│  ├─ exposure_limits.py
│  ├─ liquidity_risk.py
│  ├─ regime_killswitch.py
│  ├─ venue_risk.py
│  └─ portfolio_guardrails.py
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
│  ├─ strategy_state.py
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
├─ services/
│  ├─ trading_service.py
│  ├─ evaluation_service.py
│  ├─ portfolio_service.py
│  ├─ execution_service.py
│  ├─ strategy_service.py
│  ├─ research_factory_service.py
│  ├─ autonomous_alpha_service.py
│  └─ analytics_service.py
│
├─ api/
│  ├─ app.py
│  ├─ deps.py
│  └─ routes/
│     ├─ system.py
│     ├─ market.py
│     ├─ signals.py
│     ├─ portfolio.py
│     ├─ execution.py
│     ├─ orchestrator.py
│     ├─ strategy.py
│     ├─ research_factory.py
│     ├─ governance.py
│     ├─ alpha_factory.py
│     └─ dashboard.py
│
├─ db/
│  ├─ duckdb/
│  │  └─ v12.duckdb
│  ├─ migrations/
│  │  ├─ 001_phase_a_data.sql
│  │  ├─ 002_phase_b_signal.sql
│  │  ├─ 003_phase_c_portfolio.sql
│  │  ├─ 004_phase_d_execution.sql
│  │  ├─ 005_phase_e_orchestrator.sql
│  │  ├─ 006_phase_f_analytics.sql
│  │  ├─ 007_phase_g_strategy_os.sql
│  │  └─ 008_phase_h_research_factory.sql
│  ├─ repositories/
│  │  ├─ market_repository.py
│  │  ├─ signal_repository.py
│  │  ├─ portfolio_repository.py
│  │  ├─ execution_repository.py
│  │  ├─ strategy_repository.py
│  │  ├─ governance_repository.py
│  │  └─ alpha_repository.py
│  └─ views/
│     ├─ signal_views.sql
│     ├─ portfolio_views.sql
│     ├─ execution_views.sql
│     └─ strategy_views.sql
│
├─ monitoring/
│  ├─ healthchecks.py
│  ├─ metrics.py
│  ├─ alerts.py
│  ├─ audit.py
│  └─ incidents.py
│
├─ scheduler/
│  ├─ runner.py
│  ├─ signal_job.py
│  ├─ evaluation_job.py
│  ├─ portfolio_job.py
│  ├─ shadow_job.py
│  └─ learning_job.py
│
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ api/
│  └─ smoke/
│
└─ scripts/
   ├─ run_tests.ps1
   ├─ run_all_checks.ps1
   ├─ check_phasec.ps1
   ├─ verify_phase_d_docker.ps1
   └─ seed_demo_data.py
```

---

# 3. フェーズ別ディレクトリ対応

| Phase | 主ディレクトリ | 主な責務 |
|---|---|---|
| PhaseA | `data/`, `db/migrations/001_*` | 市場データ取得、正規化、品質管理、保存 |
| PhaseB | `signal/`, `risk/` | feature生成、regime判定、alpha生成、signal化 |
| PhaseC | `portfolio/`, `state/`, `db/migrations/003_*` | expected return、risk model、optimizer、paper portfolio |
| PhaseD | `execution/`, `db/migrations/004_*` | shadow execution、fill simulation、cost/slippage/latency |
| PhaseE | `orchestrator/`, `scheduler/` | backtest/paper/shadow/live の統一制御 |
| PhaseF | `analytics/`, `dashboard/`, `api/routes/dashboard.py` | analytics API、可視化、運転監視 |
| PhaseG | `strategy/`, `db/migrations/007_*` | strategy registry、capital allocation、global risk |
| PhaseH | `research_factory/`, `autonomous_alpha/`, `db/migrations/008_*` | experiment管理、governance、alpha factory |

---

# 4. ファイル名一覧（主要実装ファイル）

## 4.1 app/

```text
app/main.py
app/startup.py
app/shutdown.py
app/container.py
app/mode_controller.py
```

- `main.py`: アプリ起動エントリ
- `startup.py`: DB接続、scheduler、service初期化
- `shutdown.py`: graceful shutdown
- `container.py`: dependency injection
- `mode_controller.py`: backtest/paper/shadow/live の mode 管理

## 4.2 core/

```text
core/config.py
core/settings.py
core/enums.py
core/ids.py
core/clock.py
core/logging.py
core/exceptions.py
core/types.py
```

- `types.py`: Signal / AlphaResult / PortfolioAllocation / ShadowOrder など共通 dataclass

## 4.3 data/

```text
data/collectors/market_ws.py
data/collectors/market_rest.py
data/collectors/klines_collector.py
data/collectors/funding_collector.py
data/collectors/oi_collector.py
data/collectors/orderbook_collector.py
data/collectors/liquidation_collector.py
data/collectors/news_collector.py
data/collectors/onchain_collector.py

data/normalization/symbol_mapper.py
data/normalization/schema_normalizer.py
data/normalization/timestamp_aligner.py

data/quality/freshness_checks.py
data/quality/anomaly_checks.py
data/quality/gap_detector.py
data/quality/data_quality_engine.py

data/contracts/market_snapshot.py
data/contracts/orderbook_snapshot.py
data/contracts/funding_snapshot.py
data/contracts/oi_snapshot.py

data/storage/parquet_store.py
data/storage/duckdb_store.py
data/storage/jsonl_logger.py

data/replay/event_replayer.py
```

## 4.4 signal/

```text
signal/features/feature_pipeline.py
signal/features/feature_registry.py
signal/features/price_features.py
signal/features/volatility_features.py
signal/features/funding_features.py
signal/features/oi_features.py
signal/features/orderflow_features.py
signal/features/volume_features.py
signal/features/liquidation_features.py
signal/features/microstructure_features.py

signal/regime/regime_classifier.py
signal/regime/market_state.py
signal/regime/regime_filter.py

signal/alpha/alpha_router.py
signal/alpha/alpha_registry.py
signal/alpha/alpha_library.py
signal/alpha/trend_alpha.py
signal/alpha/mean_reversion_alpha.py
signal/alpha/breakout_alpha.py
signal/alpha/funding_squeeze_alpha.py
signal/alpha/oi_divergence_alpha.py
signal/alpha/liquidation_hunt_alpha.py
signal/alpha/orderbook_imbalance_alpha.py
signal/alpha/volume_spike_alpha.py

signal/metadata/alpha_metadata.py
signal/metadata/signal_signature.py

signal/signal_quality/quality_model.py

signal/evaluation/signal_evaluator.py
signal/evaluation/forward_returns.py
signal/evaluation/mfe_mae.py
signal/evaluation/target_stop_eval.py
signal/evaluation/regime_analysis.py

signal/signal_service.py
```

## 4.5 portfolio/

```text
portfolio/expected_return/expected_return_model.py
portfolio/risk_model/covariance_model.py
portfolio/risk_model/factor_risk_model.py
portfolio/risk_model/exposure_model.py
portfolio/optimizer/portfolio_optimizer.py
portfolio/optimizer/constraints.py
portfolio/optimizer/allocator.py
portfolio/dedup/signal_deduplicator.py
portfolio/overlap/overlap_manager.py
portfolio/overlap/conflict_resolver.py
portfolio/diagnostics/portfolio_diagnostics.py
portfolio/diagnostics/portfolio_summary.py
portfolio/portfolio_service.py
```

## 4.6 state/

```text
state/market_state.py
state/signal_state.py
state/portfolio_state.py
state/order_state.py
state/position_state.py
state/account_state.py
state/pnl_state.py
state/snapshot_service.py
```

## 4.7 execution/

```text
execution/planner/execution_planner.py
execution/shadow/shadow_engine.py
execution/shadow/fill_simulator.py
execution/shadow/order_lifecycle.py
execution/shadow/cost_model.py
execution/shadow/slippage_model.py
execution/shadow/latency_model.py
execution/live/live_router.py
execution/live/order_manager.py
execution/live/exchange_adapter.py
execution/venue_router/multi_venue_router.py
execution/microstructure/microstructure_engine.py
execution/execution_alpha/execution_alpha_engine.py
execution/execution_alpha/strategy_selector.py
execution/execution_alpha/liquidity_estimator.py
execution/execution_alpha/execution_plan.py
execution/tca/tca_engine.py
```

## 4.8 orchestrator/

```text
orchestrator/base.py
orchestrator/backtest_orchestrator.py
orchestrator/paper_orchestrator.py
orchestrator/shadow_orchestrator.py
orchestrator/live_orchestrator.py
orchestrator/cycle_runner.py
orchestrator/orchestration_service.py
```

## 4.9 analytics/

```text
analytics/signal_analytics.py
analytics/portfolio_analytics.py
analytics/execution_analytics.py
analytics/strategy_analytics.py
analytics/alpha_analytics.py
analytics/live_analytics.py
analytics/analytics_service.py
```

## 4.10 dashboard/

```text
dashboard/research_dashboard.py
dashboard/portfolio_dashboard.py
dashboard/execution_dashboard.py
dashboard/global_dashboard.py
dashboard/alpha_factory_dashboard.py
dashboard/live_dashboard.py
```

## 4.11 strategy/

```text
strategy/strategy_registry.py
strategy/strategy_runtime.py
strategy/strategy_state.py
strategy/strategy_allocator.py
strategy/capital_allocator.py
strategy/risk_budget_engine.py
strategy/cross_strategy_netting.py
strategy/strategy_service.py
```

## 4.12 research_factory/

```text
research_factory/experiment_tracker.py
research_factory/dataset_registry.py
research_factory/feature_registry.py
research_factory/validation_registry.py
research_factory/model_registry.py
research_factory/promotion_policy.py
research_factory/alpha_decay_monitor.py
research_factory/live_model_review.py
research_factory/rollback_policy.py
research_factory/governance_service.py
```

## 4.13 autonomous_alpha/

```text
autonomous_alpha/alpha_registry.py
autonomous_alpha/idea_generator.py
autonomous_alpha/alpha_builder.py
autonomous_alpha/alpha_backtester.py
autonomous_alpha/alpha_evaluator.py
autonomous_alpha/alpha_ranker.py
autonomous_alpha/alpha_factory_service.py
```

## 4.14 api/routes/

```text
api/routes/system.py
api/routes/market.py
api/routes/signals.py
api/routes/portfolio.py
api/routes/execution.py
api/routes/orchestrator.py
api/routes/strategy.py
api/routes/research_factory.py
api/routes/governance.py
api/routes/alpha_factory.py
api/routes/dashboard.py
```

---

# 5. DuckDBテーブル定義

以下は **analytics / operational 一体型 DuckDB** を前提にした推奨定義。
主キーは簡易表記、必要に応じて surrogate key を追加する。

---

## 5.1 PhaseA: Data Layer

### `market_bars`
市場OHLCVバー。

| column | type | note |
|---|---|---|
| symbol | VARCHAR | 銘柄 |
| timeframe | VARCHAR | 15m / 1h / 4h など |
| ts | TIMESTAMP | bar timestamp |
| open | DOUBLE | 始値 |
| high | DOUBLE | 高値 |
| low | DOUBLE | 安値 |
| close | DOUBLE | 終値 |
| volume | DOUBLE | 出来高 |
| venue | VARCHAR | 取引所 |
| source_run_id | VARCHAR | collector run |

### `funding_snapshots`

| column | type | note |
|---|---|---|
| symbol | VARCHAR | 銘柄 |
| ts | TIMESTAMP | snapshot time |
| funding_rate | DOUBLE | funding |
| venue | VARCHAR | venue |
| source_run_id | VARCHAR | collector run |

### `oi_snapshots`

| column | type | note |
|---|---|---|
| symbol | VARCHAR | 銘柄 |
| ts | TIMESTAMP | snapshot time |
| open_interest | DOUBLE | OI |
| venue | VARCHAR | venue |
| source_run_id | VARCHAR | collector run |

### `orderbook_snapshots`

| column | type | note |
|---|---|---|
| symbol | VARCHAR | 銘柄 |
| ts | TIMESTAMP | snapshot time |
| best_bid | DOUBLE | 最良買気配 |
| best_ask | DOUBLE | 最良売気配 |
| bid_depth | DOUBLE | bid depth |
| ask_depth | DOUBLE | ask depth |
| spread | DOUBLE | spread |
| venue | VARCHAR | venue |

### `data_quality_events`

| column | type | note |
|---|---|---|
| event_id | VARCHAR | PK |
| ts | TIMESTAMP | event time |
| symbol | VARCHAR | nullable |
| check_type | VARCHAR | freshness / gap / anomaly |
| severity | VARCHAR | info / warn / error |
| details_json | JSON | 詳細 |

---

## 5.2 PhaseB: Signal Layer

### `feature_snapshots`

| column | type | note |
|---|---|---|
| feature_snapshot_id | VARCHAR | PK |
| symbol | VARCHAR | 銘柄 |
| ts | TIMESTAMP | feature time |
| timeframe | VARCHAR | 主時間足 |
| feature_json | JSON | feature bundle |
| feature_version | VARCHAR | registry version |
| regime_hint | VARCHAR | optional |

### `regime_snapshots`

| column | type | note |
|---|---|---|
| regime_snapshot_id | VARCHAR | PK |
| symbol | VARCHAR | 銘柄 |
| ts | TIMESTAMP | 判定時刻 |
| regime | VARCHAR | trend_up/trend_down/range/panic |
| confidence | DOUBLE | 判定信頼度 |
| inputs_json | JSON | 判定根拠 |

### `signals`

| column | type | note |
|---|---|---|
| signal_id | VARCHAR | PK |
| symbol | VARCHAR | 銘柄 |
| ts | TIMESTAMP | signal time |
| side | VARCHAR | long / short |
| entry | DOUBLE | entry |
| stop | DOUBLE | stop |
| target | DOUBLE | target |
| confidence | DOUBLE | confidence |
| net_score | DOUBLE | integrated score |
| dominant_alpha | VARCHAR | alpha名 |
| dominant_alpha_family | VARCHAR | family |
| signal_horizon | VARCHAR | short/mid |
| signal_factor_type | VARCHAR | trend/flow 等 |
| signal_signature | VARCHAR | dedup key |
| portfolio_dedup_status | VARCHAR | kept / dropped |
| signal_expiry_ts | TIMESTAMP | stale防止 |

### `alpha_results`

| column | type | note |
|---|---|---|
| alpha_result_id | VARCHAR | PK |
| signal_id | VARCHAR | FK signals |
| alpha_name | VARCHAR | alpha |
| alpha_family | VARCHAR | family |
| factor_type | VARCHAR | factor type |
| primary_horizon | VARCHAR | short/mid |
| turnover_profile | VARCHAR | high/medium/low |
| direction | VARCHAR | long/short/neutral |
| score | DOUBLE | alpha score |
| confidence | DOUBLE | alpha confidence |
| metadata_json | JSON | extra |

### `signal_quality_scores`

| column | type | note |
|---|---|---|
| signal_id | VARCHAR | PK/FK |
| quality_score | DOUBLE | quality |
| quality_bucket | VARCHAR | high/medium/low |
| dynamic_threshold | DOUBLE | threshold |
| inputs_json | JSON | explainability |

### `signal_evaluations`

| column | type | note |
|---|---|---|
| evaluation_id | VARCHAR | PK |
| signal_id | VARCHAR | FK |
| evaluated_at | TIMESTAMP | 評価時刻 |
| fwd_return_15m | DOUBLE | forward return |
| fwd_return_1h | DOUBLE | forward return |
| fwd_return_4h | DOUBLE | forward return |
| mfe | DOUBLE | max favorable excursion |
| mae | DOUBLE | max adverse excursion |
| tp_hit | BOOLEAN | TP到達 |
| sl_hit | BOOLEAN | SL到達 |
| hit_rate_flag | BOOLEAN | hit判定 |

---

## 5.3 PhaseC: Portfolio Layer

### `signal_expected_returns`

| column | type | note |
|---|---|---|
| expected_return_id | VARCHAR | PK |
| signal_id | VARCHAR | FK |
| expected_return_gross | DOUBLE | gross ER |
| expected_return_net | DOUBLE | cost控除後 |
| expected_volatility | DOUBLE | 予想vol |
| expected_sharpe | DOUBLE | 予想Sharpe |
| turnover_penalty | DOUBLE | penalty |
| cost_penalty | DOUBLE | penalty |
| model_version | VARCHAR | ER model |

### `risk_covariance`

| column | type | note |
|---|---|---|
| covariance_id | VARCHAR | PK |
| as_of_ts | TIMESTAMP | snapshot time |
| symbol_x | VARCHAR | 銘柄X |
| symbol_y | VARCHAR | 銘柄Y |
| covariance | DOUBLE | covariance |
| correlation | DOUBLE | corr |
| window_name | VARCHAR | rolling window |

### `signal_exposure`

| column | type | note |
|---|---|---|
| exposure_id | VARCHAR | PK |
| signal_id | VARCHAR | FK |
| symbol | VARCHAR | symbol |
| side | VARCHAR | long/short |
| alpha_family | VARCHAR | family |
| factor_type | VARCHAR | factor |
| exposure_value | DOUBLE | normalized exposure |

### `portfolio_weights`

| column | type | note |
|---|---|---|
| portfolio_id | VARCHAR | PK part |
| signal_id | VARCHAR | PK part |
| target_weight | DOUBLE | optimizer result |
| capped_weight | DOUBLE | constraint後 |
| rank_score | DOUBLE | ranking |

### `portfolio_allocations`

| column | type | note |
|---|---|---|
| allocation_id | VARCHAR | PK |
| portfolio_id | VARCHAR | FK |
| symbol | VARCHAR | 銘柄 |
| side | VARCHAR | long/short |
| target_notional | DOUBLE | target exposure |
| target_qty | DOUBLE | quantity |
| source_signal_id | VARCHAR | source signal |

### `portfolio_risk_snapshots`

| column | type | note |
|---|---|---|
| risk_snapshot_id | VARCHAR | PK |
| portfolio_id | VARCHAR | FK |
| as_of_ts | TIMESTAMP | snapshot time |
| gross_exposure | DOUBLE | gross |
| net_exposure | DOUBLE | net |
| long_exposure | DOUBLE | long |
| short_exposure | DOUBLE | short |
| expected_volatility | DOUBLE | portfolio vol |
| expected_sharpe | DOUBLE | portfolio sharpe |
| concentration_top_weight | DOUBLE | concentration |

### `portfolio_pnl_snapshots`

| column | type | note |
|---|---|---|
| pnl_snapshot_id | VARCHAR | PK |
| portfolio_id | VARCHAR | FK |
| ts | TIMESTAMP | snapshot time |
| realized_pnl | DOUBLE | realized |
| unrealized_pnl | DOUBLE | unrealized |
| total_pnl | DOUBLE | total |
| turnover | DOUBLE | turnover |

### `portfolio_diagnostics`

| column | type | note |
|---|---|---|
| diagnostics_id | VARCHAR | PK |
| portfolio_id | VARCHAR | FK |
| ts | TIMESTAMP | diagnostics time |
| input_signal_count | INTEGER | before dedup |
| dedup_removed_count | INTEGER | removed |
| selected_count | INTEGER | kept |
| family_concentration_json | JSON | family concentration |
| overlap_penalty_summary_json | JSON | overlap summary |
| gross_exposure_pre_norm | DOUBLE | before normalize |
| gross_exposure_post_norm | DOUBLE | after normalize |

---

## 5.4 PhaseD: Execution / Shadow Layer

### `shadow_decisions`

| column | type | note |
|---|---|---|
| decision_id | VARCHAR | PK |
| portfolio_id | VARCHAR | FK |
| ts | TIMESTAMP | decision time |
| symbol | VARCHAR | symbol |
| side | VARCHAR | long/short |
| urgency | DOUBLE | urgency score |
| intended_qty | DOUBLE | intended quantity |
| venue_preference | VARCHAR | preferred venue |
| decision_json | JSON | detail |

### `shadow_orders`

| column | type | note |
|---|---|---|
| shadow_order_id | VARCHAR | PK |
| decision_id | VARCHAR | FK |
| created_ts | TIMESTAMP | created time |
| symbol | VARCHAR | symbol |
| side | VARCHAR | buy/sell |
| order_type | VARCHAR | market/limit |
| qty | DOUBLE | quantity |
| limit_price | DOUBLE | nullable |
| venue | VARCHAR | venue |
| status | VARCHAR | new/open/partial/filled/cancelled |

### `shadow_fills`

| column | type | note |
|---|---|---|
| shadow_fill_id | VARCHAR | PK |
| shadow_order_id | VARCHAR | FK |
| fill_ts | TIMESTAMP | fill time |
| fill_price | DOUBLE | price |
| fill_qty | DOUBLE | qty |
| fee | DOUBLE | fee |
| fill_ratio | DOUBLE | fill ratio |
| venue | VARCHAR | venue |

### `execution_costs`

| column | type | note |
|---|---|---|
| execution_cost_id | VARCHAR | PK |
| shadow_order_id | VARCHAR | FK |
| spread_cost | DOUBLE | spread crossing |
| slippage_cost | DOUBLE | slippage |
| impact_cost | DOUBLE | impact |
| fee_cost | DOUBLE | fee |
| total_cost | DOUBLE | total |

### `order_state_transitions`

| column | type | note |
|---|---|---|
| transition_id | VARCHAR | PK |
| shadow_order_id | VARCHAR | FK |
| transition_ts | TIMESTAMP | time |
| from_state | VARCHAR | state |
| to_state | VARCHAR | state |
| reason | VARCHAR | reason |

### `execution_quality_snapshots`

| column | type | note |
|---|---|---|
| quality_snapshot_id | VARCHAR | PK |
| shadow_order_id | VARCHAR | FK |
| as_of_ts | TIMESTAMP | time |
| arrival_price | DOUBLE | arrival |
| avg_fill_price | DOUBLE | avg fill |
| implementation_shortfall | DOUBLE | IS |
| fill_rate | DOUBLE | fill rate |
| maker_taker_mix | VARCHAR | execution mix |

### `slippage_reports`

| column | type | note |
|---|---|---|
| slippage_report_id | VARCHAR | PK |
| shadow_order_id | VARCHAR | FK |
| ts | TIMESTAMP | time |
| expected_slippage | DOUBLE | expected |
| realized_slippage | DOUBLE | realized |
| model_version | VARCHAR | slippage model |

### `latency_snapshots`

| column | type | note |
|---|---|---|
| latency_snapshot_id | VARCHAR | PK |
| shadow_order_id | VARCHAR | FK |
| ts | TIMESTAMP | time |
| decision_latency_ms | DOUBLE | decision latency |
| route_latency_ms | DOUBLE | route latency |
| fill_latency_ms | DOUBLE | fill latency |
| total_latency_ms | DOUBLE | total latency |

### `shadow_pnl_snapshots`

| column | type | note |
|---|---|---|
| shadow_pnl_snapshot_id | VARCHAR | PK |
| portfolio_id | VARCHAR | FK |
| ts | TIMESTAMP | time |
| realized_pnl | DOUBLE | realized |
| unrealized_pnl | DOUBLE | unrealized |
| net_of_cost_pnl | DOUBLE | net of cost |

---

## 5.5 PhaseE: Orchestrator / Runtime Layer

### `runner_state`

| column | type | note |
|---|---|---|
| runner_name | VARCHAR | PK |
| current_mode | VARCHAR | backtest/paper/shadow/live |
| cycle_count | BIGINT | cycle counter |
| status | VARCHAR | running/stopped/error |
| last_cycle_ts | TIMESTAMP | last cycle |
| last_error | VARCHAR | nullable |

### `orchestrator_runs`

| column | type | note |
|---|---|---|
| orchestrator_run_id | VARCHAR | PK |
| mode | VARCHAR | mode |
| started_at | TIMESTAMP | start |
| ended_at | TIMESTAMP | end |
| status | VARCHAR | success/fail |
| summary_json | JSON | run summary |

---

## 5.6 PhaseF: Analytics / Dashboard Layer

### `analytics_snapshots`

| column | type | note |
|---|---|---|
| analytics_snapshot_id | VARCHAR | PK |
| snapshot_ts | TIMESTAMP | as of |
| category | VARCHAR | signal/portfolio/execution/strategy |
| metric_name | VARCHAR | metric |
| metric_value | DOUBLE | value |
| metric_tags_json | JSON | tags |

### `dashboard_panels_state`

| column | type | note |
|---|---|---|
| panel_state_id | VARCHAR | PK |
| dashboard_name | VARCHAR | dashboard |
| panel_name | VARCHAR | panel |
| updated_at | TIMESTAMP | update time |
| payload_json | JSON | rendered data |

---

## 5.7 PhaseG: Strategy OS Layer

### `strategy_registry`

| column | type | note |
|---|---|---|
| strategy_id | VARCHAR | PK |
| strategy_name | VARCHAR | name |
| enabled | BOOLEAN | on/off |
| mode | VARCHAR | paper/shadow/live |
| capital_cap | DOUBLE | max capital |
| risk_budget | DOUBLE | budget |
| config_json | JSON | strategy config |

### `strategy_runtime_state`

| column | type | note |
|---|---|---|
| strategy_id | VARCHAR | PK |
| state_ts | TIMESTAMP | time |
| lifecycle_state | VARCHAR | init/running/paused/stopped |
| health_status | VARCHAR | ok/warn/error |
| state_json | JSON | runtime state |

### `global_capital_allocations`

| column | type | note |
|---|---|---|
| allocation_id | VARCHAR | PK |
| as_of_ts | TIMESTAMP | time |
| strategy_id | VARCHAR | FK |
| allocated_capital | DOUBLE | capital |
| allocation_weight | DOUBLE | weight |
| allocator_version | VARCHAR | allocator |

### `global_risk_snapshots`

| column | type | note |
|---|---|---|
| global_risk_snapshot_id | VARCHAR | PK |
| as_of_ts | TIMESTAMP | time |
| total_gross_exposure | DOUBLE | gross |
| total_net_exposure | DOUBLE | net |
| concentration_risk | DOUBLE | concentration |
| leverage | DOUBLE | leverage |
| drawdown | DOUBLE | drawdown |

### `strategy_performance_daily`

| column | type | note |
|---|---|---|
| strategy_id | VARCHAR | PK part |
| trading_date | DATE | PK part |
| pnl | DOUBLE | daily pnl |
| turnover | DOUBLE | turnover |
| hit_rate | DOUBLE | hit rate |
| sharpe_like | DOUBLE | daily ratio |

### `strategy_drawdown_events`

| column | type | note |
|---|---|---|
| drawdown_event_id | VARCHAR | PK |
| strategy_id | VARCHAR | FK |
| started_at | TIMESTAMP | start |
| ended_at | TIMESTAMP | end |
| max_drawdown | DOUBLE | drawdown |
| recovered | BOOLEAN | recovered flag |

### `cross_strategy_netting_logs`

| column | type | note |
|---|---|---|
| netting_log_id | VARCHAR | PK |
| as_of_ts | TIMESTAMP | time |
| symbol | VARCHAR | symbol |
| pre_net_long | DOUBLE | before |
| pre_net_short | DOUBLE | before |
| net_exposure | DOUBLE | after netting |
| details_json | JSON | details |

---

## 5.8 PhaseH: Research Factory / Governance / Alpha Factory

### `experiment_tracker`

| column | type | note |
|---|---|---|
| experiment_id | VARCHAR | PK |
| created_at | TIMESTAMP | time |
| hypothesis | VARCHAR | hypothesis |
| dataset_version | VARCHAR | dataset ref |
| feature_version | VARCHAR | feature ref |
| model_version | VARCHAR | model ref |
| params_json | JSON | hyperparams |
| result_summary_json | JSON | results |

### `dataset_registry`

| column | type | note |
|---|---|---|
| dataset_version | VARCHAR | PK |
| created_at | TIMESTAMP | time |
| source_name | VARCHAR | source |
| symbol_scope | VARCHAR | symbols |
| timeframe_scope | VARCHAR | timeframe |
| missing_rate | DOUBLE | data quality |
| quality_summary_json | JSON | quality summary |

### `feature_registry`

| column | type | note |
|---|---|---|
| feature_version | VARCHAR | PK |
| created_at | TIMESTAMP | time |
| feature_list_json | JSON | features |
| transform_config_json | JSON | config |
| compatibility_notes | VARCHAR | notes |

### `validation_registry`

| column | type | note |
|---|---|---|
| validation_id | VARCHAR | PK |
| experiment_id | VARCHAR | FK |
| validation_protocol | VARCHAR | WF/CV/stress |
| metrics_json | JSON | validation metrics |
| passed | BOOLEAN | pass/fail |
| created_at | TIMESTAMP | time |

### `model_registry`

| column | type | note |
|---|---|---|
| model_id | VARCHAR | PK |
| experiment_id | VARCHAR | FK |
| dataset_version | VARCHAR | dataset ref |
| feature_version | VARCHAR | feature ref |
| state | VARCHAR | candidate/approved/live/shadow/deprecated/rejected/rolled_back |
| validation_metrics_json | JSON | metrics |
| live_since | TIMESTAMP | nullable |
| last_review_at | TIMESTAMP | nullable |

### `model_state_transitions`

| column | type | note |
|---|---|---|
| transition_id | VARCHAR | PK |
| model_id | VARCHAR | FK |
| changed_at | TIMESTAMP | time |
| from_state | VARCHAR | from |
| to_state | VARCHAR | to |
| changed_by | VARCHAR | actor |
| reason | VARCHAR | reason |

### `promotion_reviews`

| column | type | note |
|---|---|---|
| review_id | VARCHAR | PK |
| model_id | VARCHAR | FK |
| reviewed_at | TIMESTAMP | time |
| decision | VARCHAR | approve/reject/hold |
| decision_reason | VARCHAR | rationale |
| review_payload_json | JSON | metrics snapshot |

### `alpha_decay_events`

| column | type | note |
|---|---|---|
| decay_event_id | VARCHAR | PK |
| model_id | VARCHAR | FK nullable |
| alpha_name | VARCHAR | alpha |
| detected_at | TIMESTAMP | time |
| decay_score | DOUBLE | decay score |
| regime_context | VARCHAR | context |
| details_json | JSON | details |

### `rollback_events`

| column | type | note |
|---|---|---|
| rollback_event_id | VARCHAR | PK |
| model_id | VARCHAR | FK |
| triggered_at | TIMESTAMP | time |
| rollback_reason | VARCHAR | reason |
| target_model_id | VARCHAR | rollback target |
| payload_json | JSON | details |

### `alpha_registry`

| column | type | note |
|---|---|---|
| alpha_id | VARCHAR | PK |
| alpha_name | VARCHAR | name |
| alpha_family | VARCHAR | family |
| factor_type | VARCHAR | type |
| primary_horizon | VARCHAR | horizon |
| turnover_profile | VARCHAR | turnover |
| feature_dependencies_json | JSON | dependencies |
| execution_style | VARCHAR | passive/taker etc |
| lifecycle_state | VARCHAR | candidate/incubating/paper/scaled/retired |

### `alpha_candidates`

| column | type | note |
|---|---|---|
| candidate_id | VARCHAR | PK |
| generated_at | TIMESTAMP | time |
| alpha_id | VARCHAR | FK |
| source_type | VARCHAR | manual/auto/llm |
| hypothesis | VARCHAR | hypothesis |
| candidate_code_ref | VARCHAR | code ref |

### `alpha_evaluations`

| column | type | note |
|---|---|---|
| alpha_evaluation_id | VARCHAR | PK |
| alpha_id | VARCHAR | FK |
| evaluated_at | TIMESTAMP | time |
| ic | DOUBLE | IC |
| sharpe | DOUBLE | Sharpe |
| hit_rate | DOUBLE | hit rate |
| max_drawdown | DOUBLE | drawdown |
| turnover | DOUBLE | turnover |
| decay_score | DOUBLE | decay |
| cost_adjusted_score | DOUBLE | net score |
| metrics_json | JSON | detail |

### `alpha_rankings`

| column | type | note |
|---|---|---|
| ranking_id | VARCHAR | PK |
| ranked_at | TIMESTAMP | time |
| alpha_id | VARCHAR | FK |
| rank_value | INTEGER | rank |
| ranking_score | DOUBLE | score |
| ranking_bucket | VARCHAR | top/core/monitor |

### `alpha_library`

| column | type | note |
|---|---|---|
| alpha_id | VARCHAR | PK |
| current_version | VARCHAR | version |
| active_flag | BOOLEAN | active |
| deployment_status | VARCHAR | research/paper/shadow/live |
| library_payload_json | JSON | canonical alpha object |

### `alpha_factory_runs`

| column | type | note |
|---|---|---|
| alpha_factory_run_id | VARCHAR | PK |
| started_at | TIMESTAMP | start |
| ended_at | TIMESTAMP | end |
| status | VARCHAR | success/fail |
| generated_count | INTEGER | generated alphas |
| promoted_count | INTEGER | promoted alphas |
| summary_json | JSON | summary |

---

# 6. テーブル導入順（migration順）

```text
001_phase_a_data.sql
  - market_bars
  - funding_snapshots
  - oi_snapshots
  - orderbook_snapshots
  - data_quality_events

002_phase_b_signal.sql
  - feature_snapshots
  - regime_snapshots
  - signals
  - alpha_results
  - signal_quality_scores
  - signal_evaluations

003_phase_c_portfolio.sql
  - signal_expected_returns
  - risk_covariance
  - signal_exposure
  - portfolio_weights
  - portfolio_allocations
  - portfolio_risk_snapshots
  - portfolio_pnl_snapshots
  - portfolio_diagnostics

004_phase_d_execution.sql
  - shadow_decisions
  - shadow_orders
  - shadow_fills
  - execution_costs
  - order_state_transitions
  - execution_quality_snapshots
  - slippage_reports
  - latency_snapshots
  - shadow_pnl_snapshots

005_phase_e_orchestrator.sql
  - runner_state
  - orchestrator_runs

006_phase_f_analytics.sql
  - analytics_snapshots
  - dashboard_panels_state

007_phase_g_strategy_os.sql
  - strategy_registry
  - strategy_runtime_state
  - global_capital_allocations
  - global_risk_snapshots
  - strategy_performance_daily
  - strategy_drawdown_events
  - cross_strategy_netting_logs

008_phase_h_research_factory.sql
  - experiment_tracker
  - dataset_registry
  - feature_registry
  - validation_registry
  - model_registry
  - model_state_transitions
  - promotion_reviews
  - alpha_decay_events
  - rollback_events
  - alpha_registry
  - alpha_candidates
  - alpha_evaluations
  - alpha_rankings
  - alpha_library
  - alpha_factory_runs
```

---

# 7. 実装上の基本ルール

1. **JSONL を raw event log、DuckDB を analytics / operational query 用**とする。  
2. **Signal / Portfolio / Execution / Strategy / Governance** は別テーブルで責務分離する。  
3. **state系は snapshot、event系は append-only** を原則とする。  
4. **model / alpha / strategy** は registry で version 管理する。  
5. **dashboard は DuckDB 集計を読むだけ**に寄せ、業務ロジックを持たせない。  
6. **paper / shadow / live** は orchestrator mode だけ変え、契約オブジェクトは可能な限り共通化する。  

---

# 8. 最終要点

この構成で、V12は次を一貫して扱える。

- PhaseA〜B: data → feature → alpha → signal
- PhaseC〜D: portfolio → shadow execution
- PhaseE〜F: orchestrator → analytics/dashboard
- PhaseG〜H: strategy OS → research governance → autonomous alpha factory

つまり、**Research / Portfolio / Execution / Governance / Alpha Factory を単一の IntegratedApp として実装できる土台**になる。

