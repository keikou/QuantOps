from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import json
from typing import Any, Iterator

try:
    import duckdb  # type: ignore
except Exception:  # pragma: no cover
    duckdb = None
    import sqlite3


class Sprint5CStore:
    def __init__(self, path: Path) -> None:
        self.path = path if duckdb is not None else path.with_suffix('.sqlite3')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def connect(self) -> Iterator[Any]:
        if duckdb is not None:
            conn = duckdb.connect(str(self.path))
        else:
            conn = sqlite3.connect(str(self.path))
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
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
                )
                """
            )
            conn.execute(
                """
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
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analytics_alpha_metrics (
                    run_id VARCHAR,
                    created_at TIMESTAMP,
                    information_coefficient DOUBLE,
                    ic_decay_1 DOUBLE,
                    signal_turnover DOUBLE,
                    candidate_count BIGINT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS strategy_risk_budgets (
                    run_id VARCHAR,
                    created_at TIMESTAMP,
                    strategy_id VARCHAR,
                    sharpe DOUBLE,
                    drawdown DOUBLE,
                    risk_budget DOUBLE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS regime_states (
                    run_id VARCHAR,
                    created_at TIMESTAMP,
                    regime VARCHAR,
                    volatility DOUBLE,
                    correlation DOUBLE,
                    trend_score DOUBLE
                )
                """
            )

    def insert_risk_snapshot(self, snapshot: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO risk_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    snapshot['run_id'], snapshot['created_at'], snapshot['gross_exposure'], snapshot['net_exposure'],
                    snapshot['max_position_weight'], snapshot['portfolio_volatility'], snapshot['drawdown'],
                    json.dumps(snapshot.get('sector_exposure', {})), json.dumps(snapshot.get('strategy_exposure', {})),
                    snapshot['risk_flag'], json.dumps(snapshot.get('risk_reasons', [])),
                ],
            )

    def insert_performance_snapshot(self, snapshot: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO analytics_performance VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    snapshot['run_id'], snapshot['created_at'], snapshot['daily_return'], snapshot['cumulative_return'],
                    snapshot['volatility'], snapshot['sharpe'], snapshot['sortino'], snapshot['max_drawdown'], snapshot['turnover'],
                ],
            )

    def insert_alpha_metrics_snapshot(self, snapshot: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO analytics_alpha_metrics VALUES (?, ?, ?, ?, ?, ?)",
                [
                    snapshot['run_id'], snapshot['created_at'], snapshot['information_coefficient'],
                    snapshot['ic_decay_1'], snapshot['signal_turnover'], snapshot['candidate_count'],
                ],
            )

    def insert_strategy_risk_budgets(self, run_id: str, created_at: str, budgets: list[dict[str, Any]]) -> None:
        with self.connect() as conn:
            for row in budgets:
                conn.execute(
                    "INSERT INTO strategy_risk_budgets VALUES (?, ?, ?, ?, ?, ?)",
                    [run_id, created_at, row.get('strategy_id', 'default'), row.get('sharpe', 0.0), row.get('drawdown', 0.0), row.get('risk_budget', 0.0)],
                )

    def insert_regime_state(self, run_id: str, created_at: str, state: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO regime_states VALUES (?, ?, ?, ?, ?, ?)",
                [run_id, created_at, state.get('regime'), state.get('volatility'), state.get('correlation'), state.get('trend_score')],
            )

    def latest_risk(self) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM risk_snapshots ORDER BY created_at DESC LIMIT 1').fetchone()
        return self._risk_row_to_dict(row)

    def risk_history(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM risk_snapshots ORDER BY created_at DESC LIMIT ?', [limit]).fetchall()
        return [self._risk_row_to_dict(r) for r in rows]

    def latest_performance(self) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM analytics_performance ORDER BY created_at DESC LIMIT 1').fetchone()
        return self._row_to_dict(['run_id','created_at','daily_return','cumulative_return','volatility','sharpe','sortino','max_drawdown','turnover'], row)

    def latest_alpha_metrics(self) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM analytics_alpha_metrics ORDER BY created_at DESC LIMIT 1').fetchone()
        return self._row_to_dict(['run_id','created_at','information_coefficient','ic_decay_1','signal_turnover','candidate_count'], row)

    def latest_budgets(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            run_row = conn.execute('SELECT run_id FROM strategy_risk_budgets ORDER BY created_at DESC LIMIT 1').fetchone()
            if not run_row:
                return []
            rows = conn.execute('SELECT * FROM strategy_risk_budgets WHERE run_id = ?', [run_row[0]]).fetchall()
        keys = ['run_id','created_at','strategy_id','sharpe','drawdown','risk_budget']
        return [self._row_to_dict(keys, r) for r in rows]

    def latest_regime(self) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM regime_states ORDER BY created_at DESC LIMIT 1').fetchone()
        return self._row_to_dict(['run_id','created_at','regime','volatility','correlation','trend_score'], row)

    def _row_to_dict(self, keys: list[str], row: Any) -> dict[str, Any]:
        if row is None:
            return {}
        return {k: row[i] for i, k in enumerate(keys)}

    def _risk_row_to_dict(self, row: Any) -> dict[str, Any]:
        if row is None:
            return {}
        return {
            'run_id': row[0],
            'created_at': row[1],
            'gross_exposure': row[2],
            'net_exposure': row[3],
            'max_position_weight': row[4],
            'portfolio_volatility': row[5],
            'drawdown': row[6],
            'sector_exposure': json.loads(row[7]) if row[7] else {},
            'strategy_exposure': json.loads(row[8]) if row[8] else {},
            'risk_flag': row[9],
            'risk_reasons': json.loads(row[10]) if row[10] else [],
        }
