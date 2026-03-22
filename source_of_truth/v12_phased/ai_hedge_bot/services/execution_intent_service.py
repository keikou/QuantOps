from __future__ import annotations

from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.core.utils import make_id, utc_now
from ai_hedge_bot.execution.shadow_models import ExecutionIntent


class ExecutionIntentService:
    def build_intents(self, portfolio_id: str, portfolio_weights: list, portfolio_allocations: list, latest_prices: dict[str, float]) -> list[ExecutionIntent]:
        alloc_by_signal = {item.signal_id: item for item in portfolio_allocations}
        out: list[ExecutionIntent] = []
        now = utc_now()
        for weight in portfolio_weights:
            allocation = alloc_by_signal.get(weight.signal_id)
            target_notional = float(getattr(allocation, 'notional_usd', 0.0) if allocation else 0.0)
            if target_notional < SETTINGS.shadow_min_notional_usd:
                continue
            urgency = 'high' if weight.target_weight >= 0.20 else 'normal' if weight.target_weight >= 0.08 else 'low'
            out.append(ExecutionIntent(
                decision_id=make_id('sdec', f'{portfolio_id}|{weight.signal_id}|{now.isoformat()}'),
                portfolio_id=portfolio_id,
                signal_id=weight.signal_id,
                symbol=weight.symbol,
                side=weight.side,
                target_weight=weight.target_weight,
                target_notional_usd=round(target_notional, 6),
                urgency=urgency,
                max_slice=round(min(weight.target_weight, SETTINGS.shadow_max_participation_rate), 6),
                decision_ts=now,
                market_snapshot_ts=now,
            ))
        return out
