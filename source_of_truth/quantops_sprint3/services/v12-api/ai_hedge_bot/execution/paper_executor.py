from __future__ import annotations

from ai_hedge_bot.core.types import PortfolioIntent, Fill, PositionState
from ai_hedge_bot.core.utils import utc_now


class PaperExecutor:
    def __init__(self) -> None:
        self.positions: dict[str, PositionState] = {}

    def execute(self, intents: list[PortfolioIntent], latest_prices: dict[str, float]) -> list[Fill]:
        fills: list[Fill] = []
        for intent in intents:
            price = latest_prices[intent.symbol]
            fill = Fill(intent.signal_id, intent.symbol, intent.side, price, intent.target_weight, utc_now())
            fills.append(fill)
            self.positions[intent.symbol] = PositionState(intent.symbol, intent.side, intent.target_weight, price, price, 0.0)
        return fills

    def mark_to_market(self, latest_prices: dict[str, float]) -> list[PositionState]:
        out = []
        for symbol, pos in self.positions.items():
            mark = latest_prices.get(symbol, pos.mark_price)
            sign = 1 if pos.side == 'long' else -1
            pnl = (mark - pos.avg_price) * pos.quantity * sign
            out.append(PositionState(symbol, pos.side, pos.quantity, pos.avg_price, mark, pnl))
        return out
