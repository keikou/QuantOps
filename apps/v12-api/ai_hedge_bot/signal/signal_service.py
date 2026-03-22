from __future__ import annotations

import math
from datetime import datetime, timezone

from ai_hedge_bot.core.enums import Side, Regime
from ai_hedge_bot.core.ids import new_signal_id
from ai_hedge_bot.core.phaseg_types import SignalCandidate
from ai_hedge_bot.core.clock import utc_now_iso


class SignalService:
    def generate(self, symbols: list[str]) -> list[dict]:
        now = datetime.now(timezone.utc)
        minute_bucket = now.hour * 60 + now.minute
        drift = math.sin(minute_bucket / 11.0)

        results = []
        for idx, symbol in enumerate(symbols):
            phase = minute_bucket / (5.0 + idx)
            raw_score = (
                0.58
                + 0.18 * math.sin(phase)
                + 0.08 * math.cos(phase / 2.0 + idx)
                + 0.03 * drift
            )
            score = round(max(0.05, min(0.95, raw_score)), 4)
            side = Side.LONG if math.sin(phase + idx) >= 0 else Side.SHORT

            if abs(drift) < 0.25:
                regime = Regime.NEUTRAL
            elif abs(drift) > 0.85:
                regime = Regime.VOLATILE
            else:
                regime = Regime.TREND if drift > 0 else Regime.MEAN_REVERSION

            sig = SignalCandidate(
                signal_id=new_signal_id(),
                symbol=symbol,
                side=side,
                score=score,
                dominant_alpha="phase6_dynamic_alpha",
                alpha_family="cross_sectional",
                horizon="intraday",
                turnover_profile="medium",
                regime=regime,
                metadata={
                    "source": "phase6_dynamic_signal",
                    "generated_at": utc_now_iso(),
                    "minute_bucket": minute_bucket,
                    "drift": round(drift, 6),
                },
            )
            results.append(sig.to_dict())

        return results