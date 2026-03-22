-- PhaseG Sprint3 DuckDB migration
CREATE TABLE IF NOT EXISTS analytics_signal_summary (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS analytics_portfolio_summary (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS analytics_execution_summary (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS analytics_shadow_summary (ts TIMESTAMP, payload JSON);
CREATE TABLE IF NOT EXISTS analytics_mode_comparison (ts TIMESTAMP, payload JSON);
