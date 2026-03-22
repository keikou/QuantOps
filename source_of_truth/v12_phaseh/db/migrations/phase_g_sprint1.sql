-- PhaseG Sprint1 DuckDB migration
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
CREATE TABLE IF NOT EXISTS dataset_versions (
    ts TIMESTAMP,
    dataset_name VARCHAR,
    version VARCHAR,
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
CREATE TABLE IF NOT EXISTS signal_features (
    ts TIMESTAMP,
    signal_id VARCHAR,
    symbol VARCHAR,
    payload JSON
);
CREATE TABLE IF NOT EXISTS signal_metadata (
    ts TIMESTAMP,
    signal_id VARCHAR,
    payload JSON
);
CREATE TABLE IF NOT EXISTS signal_quality (
    ts TIMESTAMP,
    signal_id VARCHAR,
    payload JSON
);
CREATE TABLE IF NOT EXISTS signal_evaluations (
    ts TIMESTAMP,
    signal_id VARCHAR,
    payload JSON
);
CREATE TABLE IF NOT EXISTS signal_regime_snapshots (
    ts TIMESTAMP,
    symbol VARCHAR,
    payload JSON
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
