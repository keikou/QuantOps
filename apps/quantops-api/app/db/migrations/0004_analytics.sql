CREATE TABLE IF NOT EXISTS alpha_performance_snapshots (
    snapshot_id VARCHAR PRIMARY KEY,
    strategy_id VARCHAR NOT NULL,
    strategy_name VARCHAR NOT NULL,
    pnl DOUBLE NOT NULL,
    sharpe DOUBLE NOT NULL,
    drawdown DOUBLE NOT NULL,
    hit_rate DOUBLE NOT NULL,
    turnover DOUBLE NOT NULL,
    rank_score DOUBLE NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS execution_quality_snapshots (
    snapshot_id VARCHAR PRIMARY KEY,
    fill_rate DOUBLE NOT NULL,
    avg_slippage_bps DOUBLE NOT NULL,
    latency_ms_p50 DOUBLE NOT NULL,
    latency_ms_p95 DOUBLE NOT NULL,
    venue_score DOUBLE NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS strategy_runtime_state (
    strategy_id VARCHAR PRIMARY KEY,
    desired_state VARCHAR NOT NULL,
    remote_status VARCHAR NOT NULL,
    note VARCHAR,
    updated_at TIMESTAMP NOT NULL
);
