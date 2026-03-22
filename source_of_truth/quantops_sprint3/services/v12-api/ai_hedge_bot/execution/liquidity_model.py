from __future__ import annotations

from ai_hedge_bot.core.settings import SETTINGS


class LiquidityModel:
    def classify(self, price: float, qty: float, target_notional_usd: float) -> dict:
        participation = 0.0 if target_notional_usd <= 0 else min(1.0, qty * price / max(target_notional_usd, 1e-9))
        if qty <= 0.10:
            bucket = 'deep'
            fill_ratio = 1.0
            impact_mult = 0.6
            delay_ms = SETTINGS.shadow_latency_ms * 0.7
        elif qty <= 0.25:
            bucket = 'medium'
            fill_ratio = 0.85
            impact_mult = 1.0
            delay_ms = SETTINGS.shadow_latency_ms
        else:
            bucket = 'thin'
            fill_ratio = 0.60
            impact_mult = 1.7
            delay_ms = SETTINGS.shadow_latency_ms * 1.8
        impact_bps = SETTINGS.shadow_impact_bps_per_participation * max(qty, participation) * impact_mult
        return {
            'liquidity_bucket': bucket,
            'expected_fill_ratio': round(fill_ratio, 6),
            'expected_impact_bps': round(impact_bps, 6),
            'expected_delay_ms': round(delay_ms, 3),
        }
