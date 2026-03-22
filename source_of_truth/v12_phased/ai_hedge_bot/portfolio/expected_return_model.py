from __future__ import annotations

import math

from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.core.types import ExpectedReturnEstimate, Signal
from ai_hedge_bot.core.utils import utc_now


class ExpectedReturnModel:
    def estimate(self, signal: Signal) -> ExpectedReturnEstimate:
        raw_score = float(signal.net_score or 0.0)
        confidence = max(SETTINGS.confidence_floor, float(signal.confidence or 0.0))
        confidence_adjusted_score = raw_score * confidence

        normalization_scale = max(1e-9, SETTINGS.score_normalization_scale)
        normalized_score = math.tanh(confidence_adjusted_score / normalization_scale)

        expected_return_gross = min(
            SETTINGS.expected_return_cap,
            abs(normalized_score) * SETTINGS.expected_return_scale,
        )
        turnover_penalty = min(
            SETTINGS.expected_return_cap * 0.5,
            0.0005 + abs(normalized_score) * 0.0005,
        )
        cost_penalty = SETTINGS.turnover_cost_bps / 10000.0
        expected_return_net = max(0.0, expected_return_gross - turnover_penalty - cost_penalty)

        stop_distance = abs(float(signal.entry) - float(signal.stop)) / max(float(signal.entry), 1e-9)
        target_distance = abs(float(signal.target) - float(signal.entry)) / max(float(signal.entry), 1e-9)
        expected_volatility = max(0.0025, stop_distance * 0.8 + target_distance * 0.2)

        raw_sharpe = expected_return_net / expected_volatility if expected_volatility > 0 else 0.0
        expected_sharpe = min(SETTINGS.expected_sharpe_cap, raw_sharpe)

        return ExpectedReturnEstimate(
            signal_id=signal.signal_id,
            symbol=signal.symbol,
            side=signal.side,
            expected_return_gross=round(expected_return_gross, 6),
            expected_return_net=round(expected_return_net, 6),
            expected_volatility=round(expected_volatility, 6),
            expected_sharpe=round(expected_sharpe, 6),
            turnover_penalty=round(turnover_penalty, 6),
            cost_penalty=round(cost_penalty, 6),
            confidence_adjusted_score=round(confidence_adjusted_score, 6),
            timestamp=utc_now(),
        )
