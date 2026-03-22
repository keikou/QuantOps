CREATE TABLE IF NOT EXISTS runtime_mode_configs (
    mode TEXT PRIMARY KEY,
    is_enabled BOOLEAN,
    allow_external_send BOOLEAN,
    require_live_credentials BOOLEAN,
    require_hard_risk_pass BOOLEAN,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS runtime_mode_runs (
    run_id TEXT,
    runtime_mode TEXT,
    source_job_id TEXT,
    trigger_source TEXT,
    mode_policy_json TEXT,
    status TEXT,
    details_json TEXT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS validation_results (
    validation_id TEXT,
    run_id TEXT,
    runtime_mode TEXT,
    check_name TEXT,
    passed BOOLEAN,
    severity TEXT,
    details_json TEXT,
    checked_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT,
    run_id TEXT,
    runtime_mode TEXT,
    category TEXT,
    severity TEXT,
    message TEXT,
    payload_json TEXT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shadow_pnl_snapshots (
    run_id TEXT,
    created_at TEXT,
    gross_alpha_pnl_usd DOUBLE,
    net_shadow_pnl_usd DOUBLE,
    execution_drag_usd DOUBLE,
    slippage_drag_usd DOUBLE,
    fee_drag_usd DOUBLE,
    latency_drag_usd DOUBLE
);
