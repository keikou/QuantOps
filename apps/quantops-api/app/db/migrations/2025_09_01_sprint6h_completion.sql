CREATE TABLE IF NOT EXISTS position_snapshots_latest (
    symbol VARCHAR,
    strategy_id VARCHAR,
    alpha_family VARCHAR,
    signed_qty DOUBLE,
    abs_qty DOUBLE,
    side VARCHAR,
    avg_entry_price DOUBLE,
    mark_price DOUBLE,
    market_value DOUBLE,
    unrealized_pnl DOUBLE,
    realized_pnl DOUBLE,
    exposure_notional DOUBLE,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS position_snapshots_history (
    symbol VARCHAR,
    snapshot_time TIMESTAMP
);

CREATE TABLE IF NOT EXISTS equity_snapshots (
    snapshot_time TIMESTAMP,
    total_equity DOUBLE,
    cash_balance DOUBLE,
    market_value DOUBLE
);

CREATE TABLE IF NOT EXISTS cash_ledger (
    event_time TIMESTAMP,
    delta_cash DOUBLE,
    balance_after DOUBLE
);

CREATE TABLE IF NOT EXISTS market_prices_latest (
    symbol VARCHAR,
    mark_price DOUBLE,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_store (
    event_id VARCHAR PRIMARY KEY,
    event_type VARCHAR NOT NULL,
    aggregate_type VARCHAR NOT NULL,
    aggregate_id VARCHAR NOT NULL,
    venue_id VARCHAR,
    account_id VARCHAR,
    instrument_id VARCHAR,
    event_time TIMESTAMP NOT NULL,
    payload_json VARCHAR NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS fx_rates_latest (
    from_currency VARCHAR NOT NULL,
    to_currency VARCHAR NOT NULL,
    rate DOUBLE NOT NULL,
    source VARCHAR NOT NULL,
    price_time TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS discrepancy_events (
    discrepancy_id VARCHAR PRIMARY KEY,
    category VARCHAR NOT NULL,
    field_name VARCHAR NOT NULL,
    expected_value DOUBLE,
    actual_value DOUBLE,
    delta_value DOUBLE,
    severity VARCHAR NOT NULL,
    details_json VARCHAR,
    created_at TIMESTAMP NOT NULL
);

ALTER TABLE position_snapshots_latest ADD COLUMN IF NOT EXISTS venue_id VARCHAR;
ALTER TABLE position_snapshots_latest ADD COLUMN IF NOT EXISTS account_id VARCHAR;
ALTER TABLE position_snapshots_latest ADD COLUMN IF NOT EXISTS reporting_currency VARCHAR DEFAULT 'USD';

ALTER TABLE position_snapshots_history ADD COLUMN IF NOT EXISTS venue_id VARCHAR;
ALTER TABLE position_snapshots_history ADD COLUMN IF NOT EXISTS account_id VARCHAR;
ALTER TABLE position_snapshots_history ADD COLUMN IF NOT EXISTS reporting_currency VARCHAR DEFAULT 'USD';

ALTER TABLE equity_snapshots ADD COLUMN IF NOT EXISTS venue_id VARCHAR;
ALTER TABLE equity_snapshots ADD COLUMN IF NOT EXISTS account_id VARCHAR;
ALTER TABLE equity_snapshots ADD COLUMN IF NOT EXISTS reporting_currency VARCHAR DEFAULT 'USD';
ALTER TABLE equity_snapshots ADD COLUMN IF NOT EXISTS collateral_equity DOUBLE;
ALTER TABLE equity_snapshots ADD COLUMN IF NOT EXISTS available_margin DOUBLE;
ALTER TABLE equity_snapshots ADD COLUMN IF NOT EXISTS margin_utilization DOUBLE;

ALTER TABLE cash_ledger ADD COLUMN IF NOT EXISTS venue_id VARCHAR;
ALTER TABLE cash_ledger ADD COLUMN IF NOT EXISTS account_id VARCHAR;
ALTER TABLE cash_ledger ADD COLUMN IF NOT EXISTS currency VARCHAR DEFAULT 'USD';

ALTER TABLE market_prices_latest ADD COLUMN IF NOT EXISTS venue_id VARCHAR;