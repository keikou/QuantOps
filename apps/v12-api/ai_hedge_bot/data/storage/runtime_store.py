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

from datetime import datetime, timezone


    
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
    
    def ensure_paper_initial_equity(self, initial_capital: float = 100000.0) -> bool:
        with self._session() as conn:
            row = conn.execute("SELECT COUNT(*) FROM equity_snapshots").fetchone()
            existing_count = int((row or [0])[0] or 0)
            if existing_count > 0:
                return False

            now_ts = datetime.now(timezone.utc)

            conn.execute(
                """
                INSERT INTO equity_snapshots (
                    snapshot_time,
                    cash_balance,
                    gross_exposure,
                    net_exposure,
                    long_exposure,
                    short_exposure,
                    market_value,
                    unrealized_pnl,
                    realized_pnl,
                    total_equity,
                    drawdown,
                    peak_equity
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    now_ts,
                    initial_capital,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    initial_capital,
                    0.0,
                    initial_capital,
                ],
            )

            try:
                conn.commit()
            except Exception:
                pass

            return True

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
                    order_id VARCHAR,
                    client_order_id VARCHAR,
                    strategy_id VARCHAR,
                    alpha_family VARCHAR,
                    symbol VARCHAR,
                    side VARCHAR,
                    fill_qty DOUBLE,
                    fill_price DOUBLE,
                    slippage_bps DOUBLE,
                    latency_ms DOUBLE,
                    fee_bps DOUBLE,
                    bid DOUBLE,
                    ask DOUBLE,
                    arrival_mid_price DOUBLE,
                    price_source VARCHAR,
                    quote_time TIMESTAMP,
                    quote_age_sec DOUBLE,
                    fallback_reason VARCHAR,
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
                """
            if duckdb is not None:
                conn.execute(schema_sql)
            else:
                conn.executescript(schema_sql)
            
            # Backward-compatible migrations for existing runtime DB files.
            # CREATE TABLE IF NOT EXISTS does not add missing columns to an
            # already-existing table, so we patch the legacy execution_fills
            # schema here to match the richer read model expected by execution.py.
            migration_sqls = [
                "ALTER TABLE execution_fills ADD COLUMN order_id VARCHAR",
                "ALTER TABLE execution_fills ADD COLUMN client_order_id VARCHAR",
                "ALTER TABLE execution_fills ADD COLUMN strategy_id VARCHAR",
                "ALTER TABLE execution_fills ADD COLUMN alpha_family VARCHAR",
                "ALTER TABLE execution_fills ADD COLUMN bid DOUBLE",
                "ALTER TABLE execution_fills ADD COLUMN ask DOUBLE",
                "ALTER TABLE execution_fills ADD COLUMN arrival_mid_price DOUBLE",
                "ALTER TABLE execution_fills ADD COLUMN price_source VARCHAR",
                "ALTER TABLE execution_fills ADD COLUMN quote_time TIMESTAMP",
                "ALTER TABLE execution_fills ADD COLUMN quote_age_sec DOUBLE",
                "ALTER TABLE execution_fills ADD COLUMN fallback_reason VARCHAR",
            ]

            for sql in migration_sqls:
                try:
                    conn.execute(sql)
                except Exception:
                    # Column already exists, or DB is not in a state that needs this migration
                    pass

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
