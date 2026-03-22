from __future__ import annotations

from typing import Any

from ai_hedge_bot.core.types import PortfolioIntent, Fill, PositionState
from ai_hedge_bot.core.utils import utc_now


class PaperExecutor:
    def __init__(self) -> None:
        self.positions: dict[str, PositionState] = {}

    def _resolve_price(self, symbol: str, latest_prices: dict[str, Any]) -> float:
        value = latest_prices[symbol]
        if isinstance(value, dict):
            return float(value.get('mark_price') or value.get('mid') or value.get('last') or value.get('close') or 0.0)
        return float(value)

    def execute(self, intents: list[PortfolioIntent], latest_prices: dict[str, Any]) -> list[Fill]:
        fills: list[Fill] = []
        for intent in intents:
            price = self._resolve_price(intent.symbol, latest_prices)
            fill = Fill(intent.signal_id, intent.symbol, intent.side, price, intent.target_weight, utc_now())
            fills.append(fill)
            self.positions[intent.symbol] = PositionState(intent.symbol, intent.side, intent.target_weight, price, price, 0.0)
        return fills

    def mark_to_market(self, latest_prices: dict[str, Any]) -> list[PositionState]:
        out = []
        for symbol, pos in self.positions.items():
            mark = self._resolve_price(symbol, latest_prices) if symbol in latest_prices else pos.mark_price
            sign = 1 if pos.side == 'long' else -1
            pnl = (mark - pos.avg_price) * pos.quantity * sign
            out.append(PositionState(symbol, pos.side, pos.quantity, pos.avg_price, mark, pnl))
        return out
