from __future__ import annotations

from pathlib import Path
import json
import threading
from contextlib import contextmanager
from typing import Any

try:
    import duckdb  # type: ignore
except Exception:  # pragma: no cover
    duckdb = None
    import sqlite3


class RuntimeStore:
    def __init__(self, path: Path) -> None:
        self.path = path if duckdb is not None else path.with_suffix('.sqlite3')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_lock = threading.RLock()
        self._ensure_schema()

    def _create_conn(self):
        if duckdb is not None:
            return duckdb.connect(str(self.path))
        conn = sqlite3.connect(str(self.path))
        return conn

    def _conn(self):
        conn = getattr(self._local, "conn", None)
        if conn is None:
            with self._init_lock:
                conn = getattr(self._local, "conn", None)
                if conn is None:
                    conn = self._create_conn()
                    self._local.conn = conn
        return conn

    def _reset_conn(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            self._local.conn = None

    @contextmanager
    def _session(self):
        conn = self._conn()
        try:
            yield conn
        except Exception:
            self._reset_conn()
            raise

    def close(self) -> None:
        self._reset_conn()

    def _ensure_schema(self) -> None:
        with self._session() as conn:
            schema_sql = """
                CREATE TABLE IF NOT EXISTS runtime_runs (
                    run_id VARCHAR,
                    job_name VARCHAR,
                    mode VARCHAR,
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP,
                    status VARCHAR,
                    error_message VARCHAR,
                    duration_ms BIGINT,
                    triggered_by VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS runtime_run_steps (
                    step_id VARCHAR,
                    run_id VARCHAR,
                    step_name VARCHAR,
                    status VARCHAR,
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP,
                    duration_ms BIGINT,
                    error_message VARCHAR,
                    payload_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS scheduler_jobs (
                    job_id VARCHAR,
                    job_name VARCHAR,
                    cadence VARCHAR,
                    enabled BOOLEAN,
                    owner_service VARCHAR,
                    mode VARCHAR,
                    updated_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS scheduler_runs (
                    scheduler_run_id VARCHAR,
                    job_id VARCHAR,
                    run_id VARCHAR,
                    trigger_type VARCHAR,
                    status VARCHAR,
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP,
                    duration_ms BIGINT,
                    error_message VARCHAR
                );
                CREATE TABLE IF NOT EXISTS runtime_checkpoints (
                    checkpoint_id VARCHAR,
                    run_id VARCHAR,
                    checkpoint_name VARCHAR,
                    created_at TIMESTAMP,
                    payload_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS runtime_events (
                    event_id VARCHAR,
                    run_id VARCHAR,
                    cycle_id VARCHAR,
                    event_type VARCHAR,
                    reason_code VARCHAR,
                    symbol VARCHAR,
                    mode VARCHAR,
                    source VARCHAR,
                    status VARCHAR,
                    severity VARCHAR,
                    summary VARCHAR,
                    details_json VARCHAR,
                    timestamp TIMESTAMP,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS audit_logs (
                    audit_id VARCHAR,
                    category VARCHAR,
                    event_type VARCHAR,
                    run_id VARCHAR,
                    created_at TIMESTAMP,
                    payload_json VARCHAR,
                    actor VARCHAR
                );

                CREATE TABLE IF NOT EXISTS signals (
                    signal_id VARCHAR,
                    created_at TIMESTAMP,
                    symbol VARCHAR,
                    side VARCHAR,
                    score DOUBLE,
                    dominant_alpha VARCHAR,
                    alpha_family VARCHAR,
                    horizon VARCHAR,
                    turnover_profile VARCHAR,
                    regime VARCHAR,
                    metadata_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS signal_evaluations (
                    evaluation_id VARCHAR,
                    signal_id VARCHAR,
                    created_at TIMESTAMP,
                    symbol VARCHAR,
                    won BOOLEAN,
                    return_bps DOUBLE
                );
                CREATE TABLE IF NOT EXISTS portfolio_signal_decisions (
                    decision_id VARCHAR,
                    signal_id VARCHAR,
                    created_at TIMESTAMP,
                    symbol VARCHAR,
                    side VARCHAR,
                    target_weight DOUBLE
                );
                CREATE TABLE IF NOT EXISTS portfolio_diagnostics (
                    diagnostics_id VARCHAR,
                    created_at TIMESTAMP,
                    input_signals INTEGER,
                    kept_signals INTEGER,
                    crowding_flags_json VARCHAR,
                    overlap_penalty_applied BOOLEAN
                );
                CREATE TABLE IF NOT EXISTS orchestrator_runs (
                    run_id VARCHAR,
                    created_at TIMESTAMP,
                    mode VARCHAR,
                    cycle_id VARCHAR,
                    details_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS orchestrator_cycles (
                    cycle_id VARCHAR,
                    created_at TIMESTAMP,
                    run_id VARCHAR,
                    mode VARCHAR,
                    status VARCHAR
                );
                CREATE TABLE IF NOT EXISTS execution_quality_snapshots (
                    snapshot_id VARCHAR,
                    created_at TIMESTAMP,
                    run_id VARCHAR,
                    cycle_id VARCHAR,
                    mode VARCHAR,
                    order_count INTEGER,
                    fill_count INTEGER,
                    fill_rate DOUBLE,
                    avg_slippage_bps DOUBLE,
                    latency_ms_p50 DOUBLE,
                    latency_ms_p95 DOUBLE
                );
                CREATE TABLE IF NOT EXISTS shadow_orders (
                    shadow_order_id VARCHAR,
                    created_at TIMESTAMP,
                    run_id VARCHAR,
                    cycle_id VARCHAR,
                    symbol VARCHAR,
                    side VARCHAR,
                    qty DOUBLE,
                    status VARCHAR,
                    arrival_mid_price DOUBLE
                );
                CREATE TABLE IF NOT EXISTS shadow_fills (
                    fill_id VARCHAR,
                    created_at TIMESTAMP,
                    shadow_order_id VARCHAR,
                    symbol VARCHAR,
                    fill_qty DOUBLE,
                    fill_price DOUBLE,
                    slippage_bps DOUBLE,
                    fee_bps DOUBLE
                );
                CREATE TABLE IF NOT EXISTS shadow_pnl_snapshots (
                    snapshot_id VARCHAR,
                    created_at TIMESTAMP,
                    run_id VARCHAR,
                    cycle_id VARCHAR,
                    order_count INTEGER,
                    fill_count INTEGER,
                    gross_alpha_pnl_usd DOUBLE,
                    net_shadow_pnl_usd DOUBLE,
                    execution_drag_usd DOUBLE,
                    slippage_drag_usd DOUBLE,
                    fee_drag_usd DOUBLE,
                    latency_drag_usd DOUBLE
                );

                CREATE TABLE IF NOT EXISTS alpha_signal_snapshots (
                    snapshot_id VARCHAR,
                    created_at TIMESTAMP,
                    run_id VARCHAR,
                    mode VARCHAR,
                    signal_count INTEGER,
                    symbols_json VARCHAR,
                    summary_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS alpha_candidates (
                    candidate_id VARCHAR,
                    created_at TIMESTAMP,
                    strategy_id VARCHAR,
                    alpha_family VARCHAR,
                    symbol VARCHAR,
                    side VARCHAR,
                    score DOUBLE,
                    state VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    snapshot_id VARCHAR,
                    created_at TIMESTAMP,
                    run_id VARCHAR,
                    mode VARCHAR,
                    target_count INTEGER,
                    gross_exposure DOUBLE,
                    net_exposure DOUBLE,
                    turnover_estimate DOUBLE,
                    cash_fraction DOUBLE,
                    summary_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS portfolio_positions (
                    position_id VARCHAR,
                    created_at TIMESTAMP,
                    run_id VARCHAR,
                    mode VARCHAR,
                    symbol VARCHAR,
                    side VARCHAR,
                    target_weight DOUBLE,
                    notional_usd DOUBLE,
                    source_signal_id VARCHAR
                );
                CREATE TABLE IF NOT EXISTS rebalance_plans (
                    plan_id VARCHAR,
                    created_at TIMESTAMP,
                    run_id VARCHAR,
                    mode VARCHAR,
                    action_count INTEGER,
                    gross_delta DOUBLE,
                    summary_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS execution_plans (
                    plan_id VARCHAR,
                    created_at TIMESTAMP,
                    run_id VARCHAR,
                    mode VARCHAR,
                    symbol VARCHAR,
                    side VARCHAR,
                    target_weight DOUBLE,
                    order_qty DOUBLE,
                    limit_price DOUBLE,
                    participation_rate DOUBLE,
                    status VARCHAR,
                    algo VARCHAR,
                    route VARCHAR,
                    expire_seconds INTEGER,
                    slice_count INTEGER,
                    metadata_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS execution_fills (
                    fill_id VARCHAR,
                    created_at TIMESTAMP,
                    run_id VARCHAR,
                    mode VARCHAR,
                    plan_id VARCHAR,
                    symbol VARCHAR,
                    side VARCHAR,
                    fill_qty DOUBLE,
                    fill_price DOUBLE,
                    slippage_bps DOUBLE,
                    latency_ms DOUBLE,
                    fee_bps DOUBLE,
                    status VARCHAR
                );
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


                CREATE TABLE IF NOT EXISTS experiment_tracker (
                    experiment_id VARCHAR,
                    created_at TIMESTAMP,
                    dataset_version VARCHAR,
                    feature_version VARCHAR,
                    model_version VARCHAR,
                    alpha_id VARCHAR,
                    strategy_id VARCHAR,
                    hypothesis VARCHAR,
                    hyperparameters_json VARCHAR,
                    validation_result_json VARCHAR,
                    notes VARCHAR,
                    immutable_record BOOLEAN
                );
                CREATE TABLE IF NOT EXISTS dataset_registry (
                    dataset_id VARCHAR,
                    registered_at TIMESTAMP,
                    dataset_version VARCHAR,
                    source VARCHAR,
                    symbol_scope_json VARCHAR,
                    timeframe VARCHAR,
                    missing_rate DOUBLE,
                    quality_summary_json VARCHAR,
                    drift_summary_json VARCHAR,
                    created_by VARCHAR
                );
                CREATE TABLE IF NOT EXISTS feature_registry (
                    feature_id VARCHAR,
                    registered_at TIMESTAMP,
                    feature_version VARCHAR,
                    feature_list_json VARCHAR,
                    transform_config_json VARCHAR,
                    normalization_config_json VARCHAR,
                    compatibility_info_json VARCHAR,
                    created_by VARCHAR
                );
                CREATE TABLE IF NOT EXISTS validation_registry (
                    validation_id VARCHAR,
                    created_at TIMESTAMP,
                    experiment_id VARCHAR,
                    walk_forward_result_json VARCHAR,
                    purged_cv_result_json VARCHAR,
                    robustness_result_json VARCHAR,
                    stress_result_json VARCHAR,
                    summary_score DOUBLE,
                    passed BOOLEAN
                );
                CREATE TABLE IF NOT EXISTS model_registry (
                    model_id VARCHAR,
                    created_at TIMESTAMP,
                    experiment_id VARCHAR,
                    dataset_version VARCHAR,
                    feature_version VARCHAR,
                    model_version VARCHAR,
                    validation_metrics_json VARCHAR,
                    state VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS model_state_transitions (
                    transition_id VARCHAR,
                    created_at TIMESTAMP,
                    model_id VARCHAR,
                    from_state VARCHAR,
                    to_state VARCHAR,
                    reason VARCHAR
                );


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

                CREATE TABLE IF NOT EXISTS analytics_signal_summary (
                    snapshot_id VARCHAR,
                    created_at TIMESTAMP,
                    signals_evaluated INTEGER,
                    winrate DOUBLE,
                    signal_count INTEGER
                );
                CREATE TABLE IF NOT EXISTS analytics_portfolio_summary (
                    snapshot_id VARCHAR,
                    created_at TIMESTAMP,
                    portfolio_count INTEGER,
                    gross_exposure_estimate DOUBLE,
                    latest_weight_count INTEGER
                );
                CREATE TABLE IF NOT EXISTS analytics_execution_summary (
                    snapshot_id VARCHAR,
                    created_at TIMESTAMP,
                    avg_slippage_bps DOUBLE,
                    fill_rate DOUBLE,
                    order_count INTEGER,
                    fill_count INTEGER
                );
                CREATE TABLE IF NOT EXISTS analytics_shadow_summary (
                    snapshot_id VARCHAR,
                    created_at TIMESTAMP,
                    shadow_cycles INTEGER,
                    shadow_order_count INTEGER,
                    shadow_fill_count INTEGER,
                    latest_pnl_json VARCHAR
                );
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
                CREATE TABLE IF NOT EXISTS alpha_expression_library (
                    expression_id VARCHAR,
                    expression_hash VARCHAR,
                    formula VARCHAR,
                    ast_json VARCHAR,
                    depth INTEGER,
                    node_count INTEGER,
                    feature_set_json VARCHAR,
                    operator_set_json VARCHAR,
                    generator_type VARCHAR,
                    parent_expression_ids_json VARCHAR,
                    status VARCHAR,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_synthesis_runs (
                    run_id VARCHAR,
                    generator_type VARCHAR,
                    config_json VARCHAR,
                    requested_count INTEGER,
                    generated_count INTEGER,
                    accepted_count INTEGER,
                    rejected_count INTEGER,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    status VARCHAR
                );
                CREATE TABLE IF NOT EXISTS alpha_synthesis_candidates (
                    candidate_id VARCHAR,
                    run_id VARCHAR,
                    expression_id VARCHAR,
                    formula VARCHAR,
                    generator_type VARCHAR,
                    novelty_score DOUBLE,
                    novelty_verdict VARCHAR,
                    validation_status VARCHAR,
                    rejection_reason VARCHAR,
                    aae_submission_status VARCHAR,
                    alpha_id VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_synthesis_novelty (
                    novelty_id VARCHAR,
                    candidate_id VARCHAR,
                    expression_id VARCHAR,
                    nearest_expression_id VARCHAR,
                    exact_duplicate BOOLEAN,
                    operator_jaccard_distance DOUBLE,
                    feature_jaccard_distance DOUBLE,
                    token_distance DOUBLE,
                    novelty_score DOUBLE,
                    novelty_verdict VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_evaluation_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    candidate_count INTEGER,
                    evaluated_count INTEGER,
                    promoted_count INTEGER,
                    rejected_count INTEGER,
                    status VARCHAR
                );
                CREATE TABLE IF NOT EXISTS alpha_forward_returns (
                    run_id VARCHAR,
                    alpha_id VARCHAR,
                    horizon VARCHAR,
                    raw_forward_return DOUBLE,
                    cost_adjusted_return DOUBLE,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_evaluation_scores (
                    run_id VARCHAR,
                    alpha_id VARCHAR,
                    mean_return DOUBLE,
                    median_return DOUBLE,
                    hit_rate DOUBLE,
                    sharpe_like DOUBLE,
                    sharpe_robust DOUBLE,
                    sharpe_final DOUBLE,
                    turnover DOUBLE,
                    cost_penalty DOUBLE,
                    decay_score DOUBLE,
                    robustness_score DOUBLE,
                    overfit_risk DOUBLE,
                    redundancy_score DOUBLE,
                    final_score DOUBLE,
                    decision VARCHAR,
                    details_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_validation_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    candidate_count INTEGER,
                    validated_count INTEGER,
                    passed_count INTEGER,
                    failed_count INTEGER,
                    status VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS alpha_walk_forward_windows (
                    run_id VARCHAR,
                    alpha_id VARCHAR,
                    window_id VARCHAR,
                    train_start TIMESTAMP,
                    train_end TIMESTAMP,
                    test_start TIMESTAMP,
                    test_end TIMESTAMP,
                    symbol VARCHAR,
                    regime VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_oos_scores (
                    run_id VARCHAR,
                    alpha_id VARCHAR,
                    window_id VARCHAR,
                    sample_count INTEGER,
                    train_score DOUBLE,
                    test_score DOUBLE,
                    train_sharpe DOUBLE,
                    test_sharpe DOUBLE,
                    train_hit_rate DOUBLE,
                    test_hit_rate DOUBLE,
                    score_gap DOUBLE,
                    degradation_ratio DOUBLE,
                    passed BOOLEAN,
                    fail_reason VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_validation_summary (
                    run_id VARCHAR,
                    alpha_id VARCHAR,
                    total_windows INTEGER,
                    passed_windows INTEGER,
                    pass_rate DOUBLE,
                    mean_oos_score DOUBLE,
                    median_oos_score DOUBLE,
                    mean_degradation_ratio DOUBLE,
                    worst_window_score DOUBLE,
                    stability_score DOUBLE,
                    final_validation_score DOUBLE,
                    decision VARCHAR,
                    reason VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_ensemble_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    validated_alpha_count INTEGER,
                    candidate_ensemble_count INTEGER,
                    selected_alpha_count INTEGER,
                    portfolio_score DOUBLE,
                    status VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS alpha_ensemble_candidates (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_ids VARCHAR,
                    alpha_count INTEGER,
                    source VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_ensemble_correlations (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id_a VARCHAR,
                    alpha_id_b VARCHAR,
                    correlation DOUBLE,
                    overlap_score DOUBLE,
                    hard_redundant BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_marginal_contributions (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    contribution_to_return DOUBLE,
                    contribution_to_risk DOUBLE,
                    contribution_to_sharpe DOUBLE,
                    contribution_to_diversification DOUBLE,
                    marginal_score DOUBLE,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_ensemble_scores (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_count INTEGER,
                    expected_return_score DOUBLE,
                    expected_risk_score DOUBLE,
                    sharpe_score DOUBLE,
                    diversification_score DOUBLE,
                    stability_score DOUBLE,
                    capacity_score DOUBLE,
                    concentration_penalty DOUBLE,
                    final_ensemble_score DOUBLE,
                    decision VARCHAR,
                    reject_reason VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_ensemble_weights (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    raw_weight DOUBLE,
                    normalized_weight DOUBLE,
                    cap_adjusted_weight DOUBLE,
                    final_weight DOUBLE,
                    weight_reason VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_ensemble_selection (
                    selection_id VARCHAR,
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    selected BOOLEAN,
                    selected_alpha_ids VARCHAR,
                    portfolio_ready BOOLEAN,
                    reason VARCHAR,
                    payload_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_attribution_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    alpha_count INTEGER,
                    ensemble_count INTEGER,
                    factor_count INTEGER,
                    status VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS alpha_factor_exposures (
                    run_id VARCHAR,
                    alpha_id VARCHAR,
                    factor_name VARCHAR,
                    factor_group VARCHAR,
                    beta DOUBLE,
                    t_stat DOUBLE,
                    p_value DOUBLE,
                    exposure_strength DOUBLE,
                    exposure_direction VARCHAR,
                    significant BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_factor_model_fit (
                    run_id VARCHAR,
                    alpha_id VARCHAR,
                    model_name VARCHAR,
                    sample_count INTEGER,
                    r_squared DOUBLE,
                    adjusted_r_squared DOUBLE,
                    residual_volatility DOUBLE,
                    intercept_alpha DOUBLE,
                    intercept_t_stat DOUBLE,
                    model_valid BOOLEAN,
                    fail_reason VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_residual_alpha_scores (
                    run_id VARCHAR,
                    alpha_id VARCHAR,
                    raw_alpha_score DOUBLE,
                    factor_explained_score DOUBLE,
                    residual_alpha_score DOUBLE,
                    residual_sharpe DOUBLE,
                    residual_hit_rate DOUBLE,
                    residual_mean_return DOUBLE,
                    residual_volatility DOUBLE,
                    residual_quality VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_regime_dependency (
                    run_id VARCHAR,
                    alpha_id VARCHAR,
                    regime_name VARCHAR,
                    regime_sample_count INTEGER,
                    regime_mean_return DOUBLE,
                    regime_sharpe DOUBLE,
                    regime_hit_rate DOUBLE,
                    dependency_score DOUBLE,
                    regime_dependency_flag BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_factor_concentration (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    factor_name VARCHAR,
                    weighted_exposure DOUBLE,
                    absolute_weighted_exposure DOUBLE,
                    concentration_score DOUBLE,
                    concentration_flag BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_hidden_driver_flags (
                    run_id VARCHAR,
                    alpha_id_a VARCHAR,
                    alpha_id_b VARCHAR,
                    common_driver_score DOUBLE,
                    residual_correlation DOUBLE,
                    suspected_driver VARCHAR,
                    flag BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_economic_meaning_labels (
                    run_id VARCHAR,
                    alpha_id VARCHAR,
                    primary_label VARCHAR,
                    secondary_labels VARCHAR,
                    explanation VARCHAR,
                    confidence DOUBLE,
                    production_recommendation VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_capacity_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    alpha_count INTEGER,
                    ensemble_count INTEGER,
                    status VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS alpha_capacity (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    weight DOUBLE,
                    liquidity_score DOUBLE,
                    turnover DOUBLE,
                    impact_cost DOUBLE,
                    capacity DOUBLE,
                    crowding_score DOUBLE,
                    impact_adjusted_return DOUBLE,
                    scaling_recommendation VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_impact (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    trade_size_fraction DOUBLE,
                    impact_cost DOUBLE,
                    turnover_impact DOUBLE,
                    impact_adjusted_return DOUBLE,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_crowding (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    correlation_cluster_score DOUBLE,
                    factor_concentration DOUBLE,
                    signal_overlap DOUBLE,
                    volume_anomaly DOUBLE,
                    crowding_score DOUBLE,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS ensemble_capacity (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    total_capacity DOUBLE,
                    limiting_alpha VARCHAR,
                    scaling_recommendation VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_weighting_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    alpha_count INTEGER,
                    ensemble_count INTEGER,
                    proposal_count INTEGER,
                    status VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS alpha_live_state (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    return_signal DOUBLE,
                    capacity_signal DOUBLE,
                    liquidity_signal DOUBLE,
                    crowding_penalty DOUBLE,
                    impact_penalty DOUBLE,
                    live_evidence_score DOUBLE,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_weight_signals (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    signal_name VARCHAR,
                    signal_value DOUBLE,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_dynamic_weights (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    current_weight DOUBLE,
                    target_weight DOUBLE,
                    smoothed_weight DOUBLE,
                    final_weight DOUBLE,
                    weight_delta DOUBLE,
                    weight_change_reason VARCHAR,
                    constraint_action VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_weight_constraints (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    max_weight DOUBLE,
                    max_delta DOUBLE,
                    lower_bound DOUBLE,
                    upper_bound DOUBLE,
                    constraint_action VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_weight_proposals (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    proposal_status VARCHAR,
                    max_abs_weight_change DOUBLE,
                    constraint_event_count INTEGER,
                    mpi_intent VARCHAR,
                    lcc_review_reason VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_retirement_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    alpha_count INTEGER,
                    event_count INTEGER,
                    retirement_count INTEGER,
                    status VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS alpha_live_health (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    health_score DOUBLE,
                    deactivation_pressure DOUBLE,
                    live_evidence_score DOUBLE,
                    crowding_penalty DOUBLE,
                    impact_penalty DOUBLE,
                    weight_delta DOUBLE,
                    health_state VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_kill_switch_events (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    event_type VARCHAR,
                    severity VARCHAR,
                    event_reason VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_retirement_decisions (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    decision VARCHAR,
                    kill_switch_action VARCHAR,
                    decision_reason VARCHAR,
                    lifecycle_state VARCHAR,
                    mpi_notification VARCHAR,
                    lcc_notification VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_lifecycle_updates (
                    run_id VARCHAR,
                    alpha_id VARCHAR,
                    previous_state VARCHAR,
                    next_state VARCHAR,
                    aae_update_payload VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_kill_switch_overrides (
                    override_id VARCHAR,
                    alpha_id VARCHAR,
                    override_action VARCHAR,
                    override_reason VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_feedback_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    alpha_count INTEGER,
                    family_count INTEGER,
                    recommendation_count INTEGER,
                    status VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS alpha_realized_outcomes (
                    run_id VARCHAR,
                    ensemble_id VARCHAR,
                    alpha_id VARCHAR,
                    family_id VARCHAR,
                    outcome_class VARCHAR,
                    realized_score DOUBLE,
                    learning_signal VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_structural_motifs (
                    run_id VARCHAR,
                    family_id VARCHAR,
                    motif VARCHAR,
                    survival_score DOUBLE,
                    motif_recommendation VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_metric_predictiveness (
                    run_id VARCHAR,
                    metric_name VARCHAR,
                    predictiveness_score DOUBLE,
                    calibration_action VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_generation_priors (
                    run_id VARCHAR,
                    family_id VARCHAR,
                    motif VARCHAR,
                    prior_delta DOUBLE,
                    prior_action VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_family_performance (
                    run_id VARCHAR,
                    family_id VARCHAR,
                    alpha_count INTEGER,
                    average_realized_score DOUBLE,
                    degraded_count INTEGER,
                    family_recommendation VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_policy_recommendations (
                    run_id VARCHAR,
                    policy_area VARCHAR,
                    recommendation VARCHAR,
                    rationale VARCHAR,
                    requires_operator_approval BOOLEAN,
                    application_status VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS alpha_policy_applications (
                    application_id VARCHAR,
                    recommendation_id VARCHAR,
                    approval VARCHAR,
                    application_status VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS operational_risk_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    telemetry_points INTEGER,
                    anomaly_count INTEGER,
                    incident_count INTEGER,
                    max_risk_level VARCHAR,
                    status VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS operational_risk_metrics (
                    run_id VARCHAR,
                    metric_name VARCHAR,
                    domain VARCHAR,
                    metric_value DOUBLE,
                    baseline_value DOUBLE,
                    z_score DOUBLE,
                    threshold_value DOUBLE,
                    breach BOOLEAN,
                    severity VARCHAR,
                    entity_id VARCHAR,
                    critical BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS operational_anomalies (
                    anomaly_id VARCHAR,
                    run_id VARCHAR,
                    domain VARCHAR,
                    anomaly_type VARCHAR,
                    entity_id VARCHAR,
                    observed_value DOUBLE,
                    expected_value DOUBLE,
                    anomaly_score DOUBLE,
                    severity VARCHAR,
                    evidence_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS operational_incidents (
                    incident_id VARCHAR,
                    run_id VARCHAR,
                    incident_type VARCHAR,
                    domain VARCHAR,
                    affected_entities VARCHAR,
                    severity VARCHAR,
                    risk_level VARCHAR,
                    summary VARCHAR,
                    evidence_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS operational_risk_state (
                    state_id VARCHAR,
                    run_id VARCHAR,
                    global_risk_level VARCHAR,
                    data_risk_level VARCHAR,
                    execution_risk_level VARCHAR,
                    portfolio_risk_level VARCHAR,
                    alpha_system_risk_level VARCHAR,
                    infra_risk_level VARCHAR,
                    recommended_action VARCHAR,
                    action_required BOOLEAN,
                    reason VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS risk_response_actions (
                    action_id VARCHAR,
                    run_id VARCHAR,
                    incident_id VARCHAR,
                    action_type VARCHAR,
                    target_scope VARCHAR,
                    target_id VARCHAR,
                    requested_by VARCHAR,
                    approved BOOLEAN,
                    executed BOOLEAN,
                    execution_status VARCHAR,
                    reason VARCHAR,
                    created_at TIMESTAMP,
                    executed_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS global_kill_switch_events (
                    event_id VARCHAR,
                    run_id VARCHAR,
                    trigger_source VARCHAR,
                    trigger_reason VARCHAR,
                    risk_level VARCHAR,
                    kill_scope VARCHAR,
                    state_before VARCHAR,
                    state_after VARCHAR,
                    operator_id VARCHAR,
                    reversible BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS operational_risk_overrides (
                    override_id VARCHAR,
                    operator_id VARCHAR,
                    override_scope VARCHAR,
                    override_reason VARCHAR,
                    expires_at VARCHAR,
                    active BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS risk_response_orchestrations (
                    orchestration_id VARCHAR,
                    run_id VARCHAR,
                    event_id VARCHAR,
                    risk_level VARCHAR,
                    scope VARCHAR,
                    recommended_action VARCHAR,
                    requires_operator_approval BOOLEAN,
                    lcc_payload VARCHAR,
                    execution_payload VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS runtime_safe_mode_state (
                    orchestration_id VARCHAR,
                    risk_state VARCHAR,
                    scope VARCHAR,
                    allowed_order_modes VARCHAR,
                    blocked_order_modes VARCHAR,
                    reason VARCHAR,
                    event_id VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS risk_recovery_readiness (
                    orchestration_id VARCHAR,
                    risk_level VARCHAR,
                    required_checks VARCHAR,
                    ready BOOLEAN,
                    recovery_action VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS risk_recovery_requests (
                    recovery_request_id VARCHAR,
                    orchestration_id VARCHAR,
                    operator_id VARCHAR,
                    reason VARCHAR,
                    approved BOOLEAN,
                    request_status VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS execution_health_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    order_count INTEGER,
                    fill_count INTEGER,
                    reject_count INTEGER,
                    anomaly_count INTEGER,
                    incident_count INTEGER,
                    max_risk_level VARCHAR,
                    status VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS execution_health_metrics (
                    run_id VARCHAR,
                    broker_id VARCHAR,
                    venue_id VARCHAR,
                    metric_name VARCHAR,
                    metric_value DOUBLE,
                    baseline_value DOUBLE,
                    threshold_value DOUBLE,
                    z_score DOUBLE,
                    breach BOOLEAN,
                    severity VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS broker_health_state (
                    run_id VARCHAR,
                    broker_id VARCHAR,
                    heartbeat_ok BOOLEAN,
                    api_latency_ms DOUBLE,
                    reject_rate DOUBLE,
                    cancel_success_rate DOUBLE,
                    replace_success_rate DOUBLE,
                    position_sync_ok BOOLEAN,
                    open_order_sync_ok BOOLEAN,
                    broker_health_score DOUBLE,
                    health_state VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS venue_health_state (
                    run_id VARCHAR,
                    venue_id VARCHAR,
                    fill_rate DOUBLE,
                    realized_slippage_bps DOUBLE,
                    latency_ms DOUBLE,
                    reject_rate DOUBLE,
                    partial_fill_rate DOUBLE,
                    venue_health_score DOUBLE,
                    health_state VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS execution_anomalies (
                    anomaly_id VARCHAR,
                    run_id VARCHAR,
                    broker_id VARCHAR,
                    venue_id VARCHAR,
                    order_id VARCHAR,
                    anomaly_type VARCHAR,
                    observed_value DOUBLE,
                    expected_value DOUBLE,
                    anomaly_score DOUBLE,
                    severity VARCHAR,
                    evidence_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS execution_incidents (
                    incident_id VARCHAR,
                    run_id VARCHAR,
                    incident_type VARCHAR,
                    broker_id VARCHAR,
                    venue_id VARCHAR,
                    affected_orders VARCHAR,
                    risk_level VARCHAR,
                    recommended_action VARCHAR,
                    summary VARCHAR,
                    evidence_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS execution_safe_mode_recommendations (
                    recommendation_id VARCHAR,
                    run_id VARCHAR,
                    scope VARCHAR,
                    target_id VARCHAR,
                    recommended_mode VARCHAR,
                    allowed_order_modes VARCHAR,
                    blocked_order_modes VARCHAR,
                    reason VARCHAR,
                    requires_orc_escalation BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS data_integrity_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    feed_count INTEGER,
                    symbol_count INTEGER,
                    anomaly_count INTEGER,
                    incident_count INTEGER,
                    max_risk_level VARCHAR,
                    status VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS market_feed_health (
                    run_id VARCHAR,
                    feed_id VARCHAR,
                    freshness_seconds DOUBLE,
                    missing_ratio DOUBLE,
                    bad_tick_count INTEGER,
                    latency_ms DOUBLE,
                    coverage_ratio DOUBLE,
                    feed_health_score DOUBLE,
                    health_state VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS symbol_data_health (
                    run_id VARCHAR,
                    symbol VARCHAR,
                    latest_timestamp TIMESTAMP,
                    stale_seconds DOUBLE,
                    missing_bar_count INTEGER,
                    bad_tick_count INTEGER,
                    ohlcv_valid BOOLEAN,
                    cross_source_deviation_bps DOUBLE,
                    mark_reliable BOOLEAN,
                    health_score DOUBLE,
                    health_state VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS data_anomalies (
                    anomaly_id VARCHAR,
                    run_id VARCHAR,
                    feed_id VARCHAR,
                    symbol VARCHAR,
                    anomaly_type VARCHAR,
                    observed_value DOUBLE,
                    expected_value DOUBLE,
                    anomaly_score DOUBLE,
                    severity VARCHAR,
                    evidence_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS data_incidents (
                    incident_id VARCHAR,
                    run_id VARCHAR,
                    incident_type VARCHAR,
                    affected_scope VARCHAR,
                    affected_entities VARCHAR,
                    risk_level VARCHAR,
                    recommended_action VARCHAR,
                    summary VARCHAR,
                    evidence_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS mark_reliability_state (
                    run_id VARCHAR,
                    symbol VARCHAR,
                    mark_price DOUBLE,
                    mark_source VARCHAR,
                    source_count INTEGER,
                    cross_source_dispersion_bps DOUBLE,
                    stale_seconds DOUBLE,
                    mark_reliability_score DOUBLE,
                    reliable BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS data_safe_mode_recommendations (
                    recommendation_id VARCHAR,
                    run_id VARCHAR,
                    scope VARCHAR,
                    target_id VARCHAR,
                    recommended_mode VARCHAR,
                    reason VARCHAR,
                    allowed_order_modes VARCHAR,
                    blocked_order_modes VARCHAR,
                    requires_orc_escalation BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS orc_governance_sync_runs (
                    run_id VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    incident_count INTEGER,
                    approval_created_count INTEGER,
                    audit_event_count INTEGER,
                    override_count INTEGER,
                    status VARCHAR,
                    notes VARCHAR
                );
                CREATE TABLE IF NOT EXISTS orc_governance_incidents (
                    governance_incident_id VARCHAR,
                    source_incident_id VARCHAR,
                    source_system VARCHAR,
                    incident_type VARCHAR,
                    risk_level VARCHAR,
                    affected_scope VARCHAR,
                    target_id VARCHAR,
                    governance_status VARCHAR,
                    approval_id VARCHAR,
                    operator_id VARCHAR,
                    reason VARCHAR,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS orc_governance_audit_events (
                    audit_id VARCHAR,
                    source_system VARCHAR,
                    source_event_id VARCHAR,
                    event_type VARCHAR,
                    risk_level VARCHAR,
                    action VARCHAR,
                    target_scope VARCHAR,
                    target_id VARCHAR,
                    operator_id VARCHAR,
                    metadata_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS orc_afg_approval_links (
                    link_id VARCHAR,
                    orc_incident_id VARCHAR,
                    approval_id VARCHAR,
                    proposed_action VARCHAR,
                    approval_status VARCHAR,
                    created_at TIMESTAMP,
                    decided_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS orc_response_dispatch_audit (
                    dispatch_id VARCHAR,
                    source_incident_id VARCHAR,
                    approval_id VARCHAR,
                    dispatch_target VARCHAR,
                    action VARCHAR,
                    dispatch_status VARCHAR,
                    idempotency_key VARCHAR,
                    error_message VARCHAR,
                    created_at TIMESTAMP,
                    dispatched_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS orc_recovery_governance (
                    recovery_id VARCHAR,
                    source_incident_id VARCHAR,
                    current_risk_level VARCHAR,
                    requested_target_level VARCHAR,
                    readiness_passed BOOLEAN,
                    approval_required BOOLEAN,
                    approval_id VARCHAR,
                    status VARCHAR,
                    reason VARCHAR,
                    operator_id VARCHAR,
                    created_at TIMESTAMP,
                    decided_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS operator_actions (
                    action_id VARCHAR,
                    action_type VARCHAR,
                    target_type VARCHAR,
                    target_id VARCHAR,
                    decision VARCHAR,
                    reason VARCHAR,
                    operator_id VARCHAR,
                    source_system VARCHAR,
                    risk_level VARCHAR,
                    status VARCHAR,
                    payload_json VARCHAR,
                    created_at TIMESTAMP,
                    applied_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS pending_approvals (
                    approval_id VARCHAR,
                    source_system VARCHAR,
                    source_event_id VARCHAR,
                    target_type VARCHAR,
                    target_id VARCHAR,
                    proposed_action VARCHAR,
                    risk_level VARCHAR,
                    requires_approval BOOLEAN,
                    status VARCHAR,
                    reason VARCHAR,
                    payload_json VARCHAR,
                    idempotency_key VARCHAR,
                    created_at TIMESTAMP,
                    decided_at TIMESTAMP,
                    decided_by VARCHAR
                );
                CREATE TABLE IF NOT EXISTS governance_audit_log (
                    log_id VARCHAR,
                    event_type VARCHAR,
                    source_system VARCHAR,
                    source_event_id VARCHAR,
                    target_type VARCHAR,
                    target_id VARCHAR,
                    action VARCHAR,
                    operator_id VARCHAR,
                    decision VARCHAR,
                    risk_level VARCHAR,
                    metadata_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS operator_overrides (
                    override_id VARCHAR,
                    target_type VARCHAR,
                    target_id VARCHAR,
                    override_action VARCHAR,
                    reason VARCHAR,
                    operator_id VARCHAR,
                    risk_level VARCHAR,
                    expires_at TIMESTAMP,
                    active BOOLEAN,
                    blocked_by_policy BOOLEAN,
                    created_at TIMESTAMP,
                    expired_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS governance_state (
                    state_id VARCHAR,
                    global_mode VARCHAR,
                    approval_required_level VARCHAR,
                    active_override_count INTEGER,
                    pending_approval_count INTEGER,
                    blocked_action_count INTEGER,
                    last_operator_action_id VARCHAR,
                    last_orc_risk_level VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS governance_dispatch_log (
                    dispatch_id VARCHAR,
                    approval_id VARCHAR,
                    source_system VARCHAR,
                    target_system VARCHAR,
                    action VARCHAR,
                    target_type VARCHAR,
                    target_id VARCHAR,
                    payload_json VARCHAR,
                    idempotency_key VARCHAR,
                    dry_run BOOLEAN,
                    dispatch_status VARCHAR,
                    error_message VARCHAR,
                    created_at TIMESTAMP,
                    dispatched_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS policy_enforcement_checks (
                    check_id VARCHAR,
                    source_system VARCHAR,
                    action_type VARCHAR,
                    target_type VARCHAR,
                    target_id VARCHAR,
                    enforcement_boundary VARCHAR,
                    decision VARCHAR,
                    reason VARCHAR,
                    constraints_json VARCHAR,
                    context_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS policy_enforcement_violations (
                    violation_id VARCHAR,
                    check_id VARCHAR,
                    violation_type VARCHAR,
                    severity VARCHAR,
                    source_system VARCHAR,
                    action_type VARCHAR,
                    target_type VARCHAR,
                    target_id VARCHAR,
                    reason VARCHAR,
                    evidence_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS runtime_enforcement_constraints (
                    constraint_id VARCHAR,
                    scope VARCHAR,
                    target_id VARCHAR,
                    constraint_type VARCHAR,
                    constraint_value VARCHAR,
                    source_system VARCHAR,
                    active BOOLEAN,
                    reason VARCHAR,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS enforcement_consistency_state (
                    state_id VARCHAR,
                    orc_risk_level VARCHAR,
                    afg_governance_mode VARCHAR,
                    lcc_state VARCHAR,
                    execution_mode VARCHAR,
                    consistent BOOLEAN,
                    inconsistency_reason VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS authorization_actors (
                    actor_id VARCHAR,
                    actor_type VARCHAR,
                    display_name VARCHAR,
                    active BOOLEAN,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS authorization_roles (
                    role_id VARCHAR,
                    role_name VARCHAR,
                    description VARCHAR,
                    max_risk_level VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS authorization_permissions (
                    permission_id VARCHAR,
                    permission_name VARCHAR,
                    action VARCHAR,
                    target_type VARCHAR,
                    scope VARCHAR,
                    max_risk_level VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS authorization_role_permissions (
                    role_id VARCHAR,
                    permission_id VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS authorization_actor_roles (
                    actor_id VARCHAR,
                    role_id VARCHAR,
                    scope VARCHAR,
                    target_id VARCHAR,
                    active BOOLEAN,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS authorization_decisions (
                    decision_id VARCHAR,
                    actor_id VARCHAR,
                    action VARCHAR,
                    target_type VARCHAR,
                    target_id VARCHAR,
                    risk_level VARCHAR,
                    decision VARCHAR,
                    reason VARCHAR,
                    matched_roles VARCHAR,
                    matched_permissions VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS authorization_audit_log (
                    audit_id VARCHAR,
                    actor_id VARCHAR,
                    event_type VARCHAR,
                    action VARCHAR,
                    target_type VARCHAR,
                    target_id VARCHAR,
                    decision VARCHAR,
                    metadata_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS postmortem_incidents (
                    incident_id VARCHAR,
                    source_system VARCHAR,
                    source_event_id VARCHAR,
                    severity VARCHAR,
                    incident_type VARCHAR,
                    affected_scope VARCHAR,
                    target_id VARCHAR,
                    lifecycle_status VARCHAR,
                    summary VARCHAR,
                    evidence_json VARCHAR,
                    detected_at TIMESTAMP,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS postmortem_reviews (
                    review_id VARCHAR,
                    incident_id VARCHAR,
                    reviewer_id VARCHAR,
                    lifecycle_status VARCHAR,
                    findings_json VARCHAR,
                    decision VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS postmortem_rca (
                    rca_id VARCHAR,
                    incident_id VARCHAR,
                    root_cause VARCHAR,
                    contributing_factors_json VARCHAR,
                    evidence_json VARCHAR,
                    confidence DOUBLE,
                    approved BOOLEAN,
                    created_at TIMESTAMP,
                    approved_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS postmortem_action_items (
                    action_item_id VARCHAR,
                    incident_id VARCHAR,
                    rca_id VARCHAR,
                    target_system VARCHAR,
                    action_type VARCHAR,
                    owner VARCHAR,
                    status VARCHAR,
                    due_at TIMESTAMP,
                    payload_json VARCHAR,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS postmortem_feedback (
                    feedback_id VARCHAR,
                    incident_id VARCHAR,
                    rca_id VARCHAR,
                    target_system VARCHAR,
                    feedback_type VARCHAR,
                    severity VARCHAR,
                    confidence DOUBLE,
                    payload_json VARCHAR,
                    requires_approval BOOLEAN,
                    approved BOOLEAN,
                    applied BOOLEAN,
                    created_at TIMESTAMP,
                    approved_at TIMESTAMP,
                    applied_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS postmortem_feedback_dispatch (
                    dispatch_id VARCHAR,
                    feedback_id VARCHAR,
                    target_system VARCHAR,
                    dispatch_status VARCHAR,
                    target_record_id VARCHAR,
                    error_message VARCHAR,
                    idempotency_key VARCHAR,
                    created_at TIMESTAMP,
                    dispatched_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS governance_audit_bundles (
                    bundle_id VARCHAR,
                    incident_id VARCHAR,
                    schema_version VARCHAR,
                    created_at TIMESTAMP,
                    previous_hash VARCHAR,
                    content_json VARCHAR,
                    content_hash VARCHAR,
                    chain_hash VARCHAR
                );
                CREATE TABLE IF NOT EXISTS governance_replay_logs (
                    replay_id VARCHAR,
                    incident_id VARCHAR,
                    bundle_id VARCHAR,
                    status VARCHAR,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    validation_errors_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS governance_decision_trace (
                    trace_id VARCHAR,
                    replay_id VARCHAR,
                    trace_type VARCHAR,
                    sequence_no INTEGER,
                    event_json VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS governance_audit_exports (
                    export_id VARCHAR,
                    bundle_id VARCHAR,
                    incident_id VARCHAR,
                    exported_at TIMESTAMP,
                    export_path VARCHAR,
                    export_hash VARCHAR
                );
                CREATE TABLE IF NOT EXISTS runtime_health_signals (
                    signal_id VARCHAR,
                    component VARCHAR,
                    signal_type VARCHAR,
                    value DOUBLE,
                    source VARCHAR,
                    observed_at TIMESTAMP,
                    metadata_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS runtime_health_snapshots (
                    snapshot_id VARCHAR,
                    system_score DOUBLE,
                    severity VARCHAR,
                    created_at TIMESTAMP,
                    components_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS runtime_health_scores (
                    score_id VARCHAR,
                    snapshot_id VARCHAR,
                    component VARCHAR,
                    score DOUBLE,
                    severity VARCHAR,
                    reason VARCHAR,
                    evaluated_at TIMESTAMP,
                    signal_ids_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS runtime_degradation_events (
                    event_id VARCHAR,
                    snapshot_id VARCHAR,
                    component VARCHAR,
                    severity VARCHAR,
                    reason VARCHAR,
                    detected_at TIMESTAMP,
                    is_active BOOLEAN
                );
                CREATE TABLE IF NOT EXISTS runtime_control_actions (
                    action_id VARCHAR,
                    degradation_event_id VARCHAR,
                    action_type VARCHAR,
                    severity VARCHAR,
                    target_component VARCHAR,
                    payload_json VARCHAR,
                    requires_governance_audit BOOLEAN,
                    executed_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS runtime_recovery_attempts (
                    recovery_id VARCHAR,
                    degradation_event_id VARCHAR,
                    strategy VARCHAR,
                    status VARCHAR,
                    detail VARCHAR,
                    created_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS live_orders (
                    live_order_id VARCHAR,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    symbol VARCHAR,
                    side VARCHAR,
                    qty DOUBLE,
                    venue VARCHAR,
                    order_type VARCHAR,
                    tif VARCHAR,
                    decision_id VARCHAR,
                    status VARCHAR,
                    venue_order_id VARCHAR,
                    metadata_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS live_fills (
                    live_fill_id VARCHAR,
                    created_at TIMESTAMP,
                    live_order_id VARCHAR,
                    venue_order_id VARCHAR,
                    symbol VARCHAR,
                    side VARCHAR,
                    fill_qty DOUBLE,
                    fill_price DOUBLE,
                    status VARCHAR,
                    metadata_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS live_account_balances (
                    balance_snapshot_id VARCHAR,
                    created_at TIMESTAMP,
                    venue VARCHAR,
                    asset VARCHAR,
                    free_balance DOUBLE,
                    locked_balance DOUBLE,
                    total_balance DOUBLE,
                    source VARCHAR
                );
                CREATE TABLE IF NOT EXISTS live_reconciliation_events (
                    reconciliation_event_id VARCHAR,
                    created_at TIMESTAMP,
                    live_order_id VARCHAR,
                    venue_order_id VARCHAR,
                    event_type VARCHAR,
                    status VARCHAR,
                    matched BOOLEAN,
                    details_json VARCHAR
                );
                CREATE TABLE IF NOT EXISTS live_incidents (
                    incident_id VARCHAR,
                    created_at TIMESTAMP,
                    category VARCHAR,
                    severity VARCHAR,
                    status VARCHAR,
                    summary VARCHAR,
                    details_json VARCHAR
                );
                """
            if duckdb is not None:
                conn.execute(schema_sql)
            else:
                conn.executescript(schema_sql)
            try:
                conn.commit()
            except Exception:
                pass

    def execute(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None, conn=None):
        if conn is not None:
            cur = conn.execute(sql, params or [])
            try:
                return cur.fetchall()
            except Exception:
                return []
        with self._session() as conn:
            cur = conn.execute(sql, params or [])
            rows = cur.fetchall()
            try:
                conn.commit()
            except Exception:
                pass
            return rows

    def append(self, table: str, rows: list[dict[str, Any]] | dict[str, Any], conn=None) -> None:
        if isinstance(rows, dict):
            rows = [rows]
        if not rows:
            return
        cols = list(rows[0].keys())
        placeholders = ', '.join(['?'] * len(cols))
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        values = [tuple(row.get(c) for c in cols) for row in rows]
        if conn is not None:
            conn.executemany(sql, values)
            return
        with self._session() as conn:
            conn.executemany(sql, values)
            try:
                conn.commit()
            except Exception:
                pass

    def fetchone_dict(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        with self._session() as conn:
            cur = conn.execute(sql, params or [])
            row = cur.fetchone()
            if row is None:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))

    def fetchall_dict(self, sql: str, params: list[Any] | tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        with self._session() as conn:
            cur = conn.execute(sql, params or [])
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in rows]

    @staticmethod
    def to_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)

    @staticmethod
    def parse_json(value: Any, default: Any = None) -> Any:
        if value in (None, ""):
            return default
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(str(value))
        except Exception:
            return default
