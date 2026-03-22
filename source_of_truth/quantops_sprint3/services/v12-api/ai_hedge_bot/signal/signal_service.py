from __future__ import annotations

from ai_hedge_bot.core.enums import Side, Regime
from ai_hedge_bot.core.ids import new_signal_id
from ai_hedge_bot.core.phaseg_types import SignalCandidate
from ai_hedge_bot.core.clock import utc_now_iso


class SignalService:
    def generate(self, symbols: list[str]) -> list[dict]:
        results = []
        for idx, symbol in enumerate(symbols):
            side = Side.LONG if idx % 2 == 0 else Side.SHORT
            score = round(0.55 + (idx * 0.03), 4)
            sig = SignalCandidate(
                signal_id=new_signal_id(),
                symbol=symbol,
                side=side,
                score=score,
                dominant_alpha='phaseg_meta_alpha',
                alpha_family='cross_sectional',
                horizon='intraday',
                turnover_profile='medium',
                regime=Regime.NEUTRAL,
                metadata={'source': 'phaseg_scaffold', 'generated_at': utc_now_iso()},
            )
            results.append(sig.to_dict())
        return results
