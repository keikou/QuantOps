from __future__ import annotations

import pandas as pd

from ai_hedge_bot.core.types import Signal, EvaluationResult


class SignalEvaluator:
    def evaluate(self, signal: Signal, future_frame: pd.DataFrame) -> EvaluationResult:
        close = future_frame['close'].reset_index(drop=True)
        if len(close) < 5:
            return EvaluationResult(signal.signal_id, signal.symbol, signal.side, 0.0, 0.0, 0.0, 0.0, False)
        entry = signal.entry
        sign = 1.0 if signal.side == 'long' else -1.0
        ret_1h = sign * ((float(close.iloc[min(4, len(close)-1)]) / entry) - 1.0)
        ret_4h = sign * ((float(close.iloc[-1]) / entry) - 1.0)
        path = sign * ((close / entry) - 1.0)
        mfe = float(path.max())
        mae = float(path.min())
        hit = ret_4h > 0
        return EvaluationResult(signal.signal_id, signal.symbol, signal.side, ret_1h, ret_4h, mfe, mae, hit)
