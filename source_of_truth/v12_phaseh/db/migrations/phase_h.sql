-- PhaseH Sprint1 DuckDB migration
CREATE TABLE IF NOT EXISTS strategy_registry (
    strategy_id VARCHAR,
    name VARCHAR,
    enabled BOOLEAN,
    mode VARCHAR,
    capital_cap DOUBLE,
    risk_budget DOUBLE,
    priority INTEGER,
    alpha_family VARCHAR,
    turnover_profile VARCHAR,
    description VARCHAR,
    symbol_scope_json VARCHAR,
    side_bias VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategy_runtime_state (
    strategy_id VARCHAR,
    initialized BOOLEAN,
    last_market_ts TIMESTAMP,
    last_signal_count INTEGER,
    last_target_count INTEGER,
    last_fill_id VARCHAR,
    risk_events INTEGER,
    status VARCHAR,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS global_capital_allocations (
    allocation_id VARCHAR,
    created_at TIMESTAMP,
    strategy_id VARCHAR,
    capital_weight DOUBLE,
    capital_cap DOUBLE,
    risk_budget DOUBLE,
    score DOUBLE,
    signal_count INTEGER,
    active_symbols_json VARCHAR
);

CREATE TABLE IF NOT EXISTS cross_strategy_netting_logs (
    netting_log_id VARCHAR,
    created_at TIMESTAMP,
    symbol VARCHAR,
    gross_before DOUBLE,
    gross_after DOUBLE,
    net_exposure DOUBLE,
    contributions_json VARCHAR
);

CREATE TABLE IF NOT EXISTS global_risk_snapshots (
    snapshot_id VARCHAR,
    created_at TIMESTAMP,
    strategy_id VARCHAR,
    gross_exposure DOUBLE,
    net_exposure DOUBLE,
    capital_weight DOUBLE,
    risk_budget DOUBLE,
    budget_usage DOUBLE,
    concentration_top_symbol VARCHAR,
    concentration_top_weight DOUBLE,
    status VARCHAR
);

CREATE TABLE IF NOT EXISTS strategy_performance_daily (
    perf_id VARCHAR,
    created_at TIMESTAMP,
    strategy_id VARCHAR,
    strategy_name VARCHAR,
    capital_weight DOUBLE,
    expected_return DOUBLE,
    realized_return DOUBLE,
    hit_rate DOUBLE,
    turnover DOUBLE,
    cost_adjusted_score DOUBLE,
    drawdown DOUBLE
);

CREATE TABLE IF NOT EXISTS strategy_drawdown_events (
    event_id VARCHAR,
    created_at TIMESTAMP,
    strategy_id VARCHAR,
    severity VARCHAR,
    drawdown DOUBLE,
    notes VARCHAR
);


-- PhaseH Sprint3 DuckDB migration

                CREATE TABLE IF NOT EXISTS promotion_evaluations (
                    evaluation_id VARCHAR,
                    created_at TIMESTAMP,
                    model_id VARCHAR,
                    experiment_id VARCHAR,
                    decision VARCHAR,
                    summary_score DOUBLE,
                    cost_adjusted_score DOUBLE,
                    sample_size INTEGER,
                    max_drawdown DOUBLE,
                    regime_coverage DOUBLE,
                    slippage_bps DOUBLE,
                    reasons_json VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS model_live_reviews (
                    review_id VARCHAR,
                    created_at TIMESTAMP,
                    model_id VARCHAR,
                    strategy_id VARCHAR,
                    decision VARCHAR,
                    pnl_drift DOUBLE,
                    hit_rate DOUBLE,
                    slippage_bps DOUBLE,
                    fill_rate DOUBLE,
                    turnover DOUBLE,
                    risk_usage DOUBLE,
                    flags_json VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS alpha_drift_events (
                    event_id VARCHAR,
                    created_at TIMESTAMP,
                    model_id VARCHAR,
                    alpha_id VARCHAR,
                    symbol VARCHAR,
                    regime VARCHAR,
                    rolling_ic DOUBLE,
                    hit_rate_now DOUBLE,
                    summary_score_now DOUBLE,
                    severity VARCHAR,
                    status VARCHAR,
                    flags_json VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS rollback_events (
                    rollback_id VARCHAR,
                    created_at TIMESTAMP,
                    model_id VARCHAR,
                    trigger_reason VARCHAR,
                    selected_model_id VARCHAR,
                    selected_model_version VARCHAR,
                    selected_score DOUBLE,
                    action VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS champion_challenger_runs (
                    run_id VARCHAR,
                    created_at TIMESTAMP,
                    champion_model_id VARCHAR,
                    challenger_model_id VARCHAR,
                    champion_score DOUBLE,
                    challenger_score DOUBLE,
                    winner VARCHAR,
                    recommended_action VARCHAR,
                    capital_shift DOUBLE,
                    notes VARCHAR
                );


-- PhaseH Sprint4 DuckDB migration
CREATE TABLE IF NOT EXISTS alpha_registry (
    alpha_id VARCHAR,
    created_at TIMESTAMP,
    alpha_family VARCHAR,
    factor_type VARCHAR,
    horizon VARCHAR,
    turnover_profile VARCHAR,
    feature_dependencies_json VARCHAR,
    risk_profile VARCHAR,
    execution_sensitivity DOUBLE,
    state VARCHAR,
    source VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS alpha_experiments (
    experiment_id VARCHAR,
    created_at TIMESTAMP,
    alpha_id VARCHAR,
    generation_theme VARCHAR,
    design_json VARCHAR,
    status VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS alpha_eval_results (
    evaluation_id VARCHAR,
    created_at TIMESTAMP,
    alpha_id VARCHAR,
    test_name VARCHAR,
    summary_score DOUBLE,
    sharpe DOUBLE,
    max_drawdown DOUBLE,
    turnover DOUBLE,
    slippage_bps DOUBLE,
    fill_probability DOUBLE,
    decision VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS alpha_status_events (
    event_id VARCHAR,
    created_at TIMESTAMP,
    alpha_id VARCHAR,
    event_type VARCHAR,
    from_state VARCHAR,
    to_state VARCHAR,
    reason VARCHAR
);

CREATE TABLE IF NOT EXISTS alpha_promotions (
    promotion_id VARCHAR,
    created_at TIMESTAMP,
    alpha_id VARCHAR,
    decision VARCHAR,
    source_run_id VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS alpha_demotions (
    demotion_id VARCHAR,
    created_at TIMESTAMP,
    alpha_id VARCHAR,
    decision VARCHAR,
    source_run_id VARCHAR,
    notes VARCHAR
);

CREATE TABLE IF NOT EXISTS alpha_rankings (
    ranking_id VARCHAR,
    created_at TIMESTAMP,
    alpha_id VARCHAR,
    rank_score DOUBLE,
    expected_return DOUBLE,
    risk_adjusted_score DOUBLE,
    execution_cost_adjusted_score DOUBLE,
    diversification_value DOUBLE,
    recommended_action VARCHAR
);

CREATE TABLE IF NOT EXISTS alpha_library (
    library_id VARCHAR,
    created_at TIMESTAMP,
    alpha_id VARCHAR,
    alpha_family VARCHAR,
    factor_type VARCHAR,
    state VARCHAR,
    rank_score DOUBLE,
    usage_count INTEGER,
    tags_json VARCHAR
);
