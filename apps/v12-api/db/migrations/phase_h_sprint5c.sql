CREATE TABLE IF NOT EXISTS risk_snapshots (
    run_id VARCHAR,
    created_at TIMESTAMP,
    gross_exposure DOUBLE,
    net_exposure DOUBLE,
    max_position_weight DOUBLE,
    portfolio_volatility DOUBLE,
    drawdown DOUBLE,
    sector_exposure_json VARCHAR,
    strategy_exposure_json VARCHAR,
    risk_flag BOOLEAN,
    risk_reasons_json VARCHAR
);

CREATE TABLE IF NOT EXISTS analytics_performance (
    run_id VARCHAR,
    created_at TIMESTAMP,
    daily_return DOUBLE,
    cumulative_return DOUBLE,
    volatility DOUBLE,
    sharpe DOUBLE,
    sortino DOUBLE,
    max_drawdown DOUBLE,
    turnover DOUBLE
);

CREATE TABLE IF NOT EXISTS analytics_alpha_metrics (
    run_id VARCHAR,
    created_at TIMESTAMP,
    information_coefficient DOUBLE,
    ic_decay_1 DOUBLE,
    signal_turnover DOUBLE,
    candidate_count BIGINT
);

CREATE TABLE IF NOT EXISTS strategy_risk_budgets (
    run_id VARCHAR,
    created_at TIMESTAMP,
    strategy_id VARCHAR,
    sharpe DOUBLE,
    drawdown DOUBLE,
    risk_budget DOUBLE
);

CREATE TABLE IF NOT EXISTS regime_states (
    run_id VARCHAR,
    created_at TIMESTAMP,
    regime VARCHAR,
    volatility DOUBLE,
    correlation DOUBLE,
    trend_score DOUBLE
);
