-- PhaseG DuckDB migration skeleton
CREATE TABLE IF NOT EXISTS market_data_quality_events (
    ts TIMESTAMP,
    symbol VARCHAR,
    status VARCHAR,
    details JSON
);
CREATE TABLE IF NOT EXISTS market_feed_liveness (
    ts TIMESTAMP,
    symbol VARCHAR,
    alive BOOLEAN,
    details JSON
);
CREATE TABLE IF NOT EXISTS signals (
    signal_id VARCHAR,
    ts TIMESTAMP,
    symbol VARCHAR,
    side VARCHAR,
    score DOUBLE,
    dominant_alpha VARCHAR,
    alpha_family VARCHAR,
    horizon VARCHAR,
    turnover_profile VARCHAR,
    metadata JSON
);
CREATE TABLE IF NOT EXISTS portfolio_signal_decisions (
    ts TIMESTAMP,
    signal_id VARCHAR,
    symbol VARCHAR,
    side VARCHAR,
    target_weight DOUBLE,
    details JSON
);
CREATE TABLE IF NOT EXISTS portfolio_diagnostics (
    ts TIMESTAMP,
    input_signals INTEGER,
    kept_signals INTEGER,
    details JSON
);
CREATE TABLE IF NOT EXISTS state_market_snapshots (ts TIMESTAMP, snapshot_name VARCHAR, payload JSON);
CREATE TABLE IF NOT EXISTS state_signal_snapshots (ts TIMESTAMP, snapshot_name VARCHAR, payload JSON);
CREATE TABLE IF NOT EXISTS state_portfolio_snapshots (ts TIMESTAMP, snapshot_name VARCHAR, payload JSON);
CREATE TABLE IF NOT EXISTS state_order_snapshots (ts TIMESTAMP, snapshot_name VARCHAR, payload JSON);
CREATE TABLE IF NOT EXISTS state_position_snapshots (ts TIMESTAMP, snapshot_name VARCHAR, payload JSON);
CREATE TABLE IF NOT EXISTS state_account_snapshots (ts TIMESTAMP, snapshot_name VARCHAR, payload JSON);
CREATE TABLE IF NOT EXISTS state_pnl_snapshots (ts TIMESTAMP, snapshot_name VARCHAR, payload JSON);
CREATE TABLE IF NOT EXISTS state_recovery_checkpoints (ts TIMESTAMP, checkpoint_name VARCHAR, payload JSON);
CREATE TABLE IF NOT EXISTS orchestrator_runs (run_id VARCHAR, ts TIMESTAMP, mode VARCHAR, status VARCHAR, payload JSON);
CREATE TABLE IF NOT EXISTS orchestrator_cycles (cycle_id VARCHAR, run_id VARCHAR, ts TIMESTAMP, mode VARCHAR, status VARCHAR, payload JSON);
CREATE TABLE IF NOT EXISTS backtest_runs (run_id VARCHAR, ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS backtest_results (run_id VARCHAR, ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS paper_orders (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS paper_fills (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS paper_positions (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS paper_pnl_snapshots (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS shadow_decisions (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS shadow_orders (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS shadow_fills (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS execution_costs (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS order_events (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS order_state_transitions (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS execution_quality_snapshots (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS slippage_reports (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS latency_snapshots (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS shadow_pnl_snapshots (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS analytics_signal_summary (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS analytics_portfolio_summary (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS analytics_execution_summary (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS analytics_shadow_summary (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS analytics_mode_comparison (ts TIMESTAMP, payload JSON);
