from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Any

from ai_hedge_bot.core.clock import utc_now_iso


class StrategyRuntime(Protocol):
    strategy_id: str

    def initialize(self) -> dict[str, Any]: ...
    def on_market_data(self, market_state: dict[str, Any]) -> dict[str, Any]: ...
    def generate_signal(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]: ...
    def build_target(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]: ...
    def on_fill(self, fill: dict[str, Any]) -> dict[str, Any]: ...
    def on_risk_event(self, event: dict[str, Any]) -> dict[str, Any]: ...
    def shutdown(self) -> dict[str, Any]: ...


@dataclass
class RuntimeState:
    initialized: bool = False
    last_market_ts: str | None = None
    last_signal_count: int = 0
    last_target_count: int = 0
    last_fill_id: str | None = None
    risk_events: int = 0
    status: str = 'idle'
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            'initialized': self.initialized,
            'last_market_ts': self.last_market_ts,
            'last_signal_count': self.last_signal_count,
            'last_target_count': self.last_target_count,
            'last_fill_id': self.last_fill_id,
            'risk_events': self.risk_events,
            'status': self.status,
            'updated_at': self.updated_at,
        }


@dataclass
class SimpleStrategyRuntime:
    strategy_id: str
    symbol_scope: list[str]
    side_bias: str = 'follow'
    target_scale: float = 1.0
    state: RuntimeState = field(default_factory=RuntimeState)

    def initialize(self) -> dict[str, Any]:
        self.state.initialized = True
        self.state.status = 'initialized'
        self.state.updated_at = utc_now_iso()
        return self.state.to_dict()

    def on_market_data(self, market_state: dict[str, Any]) -> dict[str, Any]:
        self.state.last_market_ts = market_state.get('market_ts', utc_now_iso())
        self.state.status = 'market_updated'
        self.state.updated_at = utc_now_iso()
        return self.state.to_dict()

    def generate_signal(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        filtered = [s for s in signals if s.get('symbol') in self.symbol_scope]
        self.state.last_signal_count = len(filtered)
        self.state.status = 'signals_generated'
        self.state.updated_at = utc_now_iso()
        return filtered

    def build_target(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        scoped = self.generate_signal(signals)
        count = max(len(scoped), 1)
        targets: list[dict[str, Any]] = []
        for item in scoped:
            weight = round(abs(float(item.get('score', 0.0))) / count * self.target_scale, 6)
            side = item.get('side', 'long')
            if self.side_bias == 'invert':
                side = 'short' if side == 'long' else 'long'
            elif self.side_bias in {'long_only', 'short_only'}:
                side = 'long' if self.side_bias == 'long_only' else 'short'
            targets.append(
                {
                    'strategy_id': self.strategy_id,
                    'symbol': item.get('symbol'),
                    'side': side,
                    'signal_id': item.get('signal_id'),
                    'score': float(item.get('score', 0.0)),
                    'target_weight_hint': weight,
                }
            )
        self.state.last_target_count = len(targets)
        self.state.status = 'targets_built'
        self.state.updated_at = utc_now_iso()
        return targets

    def on_fill(self, fill: dict[str, Any]) -> dict[str, Any]:
        self.state.last_fill_id = fill.get('fill_id') or fill.get('shadow_order_id')
        self.state.status = 'fill_received'
        self.state.updated_at = utc_now_iso()
        return self.state.to_dict()

    def on_risk_event(self, event: dict[str, Any]) -> dict[str, Any]:
        self.state.risk_events += 1
        self.state.status = f"risk_event:{event.get('severity', 'info')}"
        self.state.updated_at = utc_now_iso()
        return self.state.to_dict()

    def shutdown(self) -> dict[str, Any]:
        self.state.status = 'shutdown'
        self.state.updated_at = utc_now_iso()
        return self.state.to_dict()
