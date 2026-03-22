CREATE TABLE IF NOT EXISTS risk_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    gross_exposure DOUBLE NOT NULL,
    net_exposure DOUBLE NOT NULL,
    leverage DOUBLE NOT NULL,
    drawdown DOUBLE NOT NULL,
    var_95 DOUBLE,
    stress_loss DOUBLE,
    risk_limit_json TEXT,
    alert_state TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    source_service TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP
);
