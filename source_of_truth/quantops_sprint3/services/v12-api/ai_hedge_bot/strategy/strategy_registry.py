from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.enums import Mode
from ai_hedge_bot.strategy.strategy_runtime import SimpleStrategyRuntime


@dataclass(frozen=True)
class StrategyDefinition:
    strategy_id: str
    name: str
    enabled: bool
    mode: str
    capital_cap: float
    risk_budget: float
    priority: int
    alpha_family: str
    turnover_profile: str
    description: str
    symbol_scope: list[str]
    side_bias: str = 'follow'

    def to_row(self) -> dict[str, Any]:
        ts = utc_now_iso()
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'enabled': self.enabled,
            'mode': self.mode,
            'capital_cap': self.capital_cap,
            'risk_budget': self.risk_budget,
            'priority': self.priority,
            'alpha_family': self.alpha_family,
            'turnover_profile': self.turnover_profile,
            'description': self.description,
            'symbol_scope_json': CONTAINER.runtime_store.to_json(self.symbol_scope),
            'side_bias': self.side_bias,
            'created_at': ts,
            'updated_at': ts,
        }


class StrategyRegistry:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        row = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM strategy_registry') or {'c': 0}
        if int(row['c'] or 0) > 0:
            return
        symbols = CONTAINER.config.symbols
        default_defs = [
            StrategyDefinition(
                strategy_id='trend_core',
                name='Trend Core',
                enabled=True,
                mode=Mode.PAPER.value,
                capital_cap=0.45,
                risk_budget=0.40,
                priority=1,
                alpha_family='trend',
                turnover_profile='medium',
                description='Momentum / trend-following sleeve for liquid majors.',
                symbol_scope=symbols[: min(3, len(symbols))],
                side_bias='follow',
            ),
            StrategyDefinition(
                strategy_id='mean_reversion_core',
                name='Mean Reversion Core',
                enabled=True,
                mode=Mode.PAPER.value,
                capital_cap=0.35,
                risk_budget=0.33,
                priority=2,
                alpha_family='mean_reversion',
                turnover_profile='high',
                description='Short-horizon contrarian sleeve for liquid pairs.',
                symbol_scope=symbols[1: min(4, len(symbols))] or symbols,
                side_bias='invert',
            ),
            StrategyDefinition(
                strategy_id='event_core',
                name='Event Core',
                enabled=True,
                mode=Mode.SHADOW.value,
                capital_cap=0.20,
                risk_budget=0.27,
                priority=3,
                alpha_family='event',
                turnover_profile='low',
                description='Event / catalyst sleeve with smaller capital footprint.',
                symbol_scope=symbols[-2:] if len(symbols) >= 2 else symbols,
                side_bias='follow',
            ),
        ]
        self.store.append('strategy_registry', [d.to_row() for d in default_defs])

    def list(self) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT strategy_id, name, enabled, mode, capital_cap, risk_budget,
                   priority, alpha_family, turnover_profile, description,
                   symbol_scope_json, side_bias, created_at, updated_at
            FROM strategy_registry
            ORDER BY priority, strategy_id
            """
        )
        for row in rows:
            scope_json = row.pop('symbol_scope_json', '[]') or '[]'
            row['symbol_scope'] = self._from_json(scope_json)
        return rows

    def active(self) -> list[dict[str, Any]]:
        return [row for row in self.list() if bool(row.get('enabled'))]

    def runtimes(self) -> list[SimpleStrategyRuntime]:
        runtimes = []
        for row in self.active():
            runtimes.append(
                SimpleStrategyRuntime(
                    strategy_id=row['strategy_id'],
                    symbol_scope=list(row.get('symbol_scope', [])),
                    side_bias=row.get('side_bias', 'follow'),
                    target_scale=float(row.get('capital_cap', 0.0) or 0.0),
                )
            )
        return runtimes

    def latest_state(self, strategy_id: str) -> dict[str, Any] | None:
        return self.store.fetchone_dict(
            """
            SELECT strategy_id, initialized, last_market_ts, last_signal_count,
                   last_target_count, last_fill_id, risk_events, status, updated_at
            FROM strategy_runtime_state
            WHERE strategy_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            [strategy_id],
        )

    @staticmethod
    def _from_json(value: str) -> list[str]:
        import json

        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
