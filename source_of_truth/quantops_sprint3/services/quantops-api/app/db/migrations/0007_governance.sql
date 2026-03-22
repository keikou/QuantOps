CREATE TABLE IF NOT EXISTS governance_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    overview_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS promotion_reviews (
    review_id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    review_type TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
