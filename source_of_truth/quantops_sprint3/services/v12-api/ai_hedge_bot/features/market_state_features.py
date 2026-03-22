from __future__ import annotations

import numpy as np
import pandas as pd


def build_market_state_features(df: pd.DataFrame) -> dict[str, pd.Series]:
    trend_strength = ((df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).mean()).fillna(0.0)
    rv_short = df['close'].pct_change().rolling(12).std().fillna(0.0)
    rv_long = df['close'].pct_change().rolling(48).std().replace(0, np.nan)
    vol_ratio = (rv_short / rv_long).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    liq_z = ((df['liquidation_volume'] - df['liquidation_volume'].rolling(30).mean()) / df['liquidation_volume'].rolling(30).std()).fillna(0.0)
    stress = (0.5 * vol_ratio + 0.5 * liq_z.abs()).fillna(0.0)
    return {
        'market_regime_score': (0.4 * trend_strength.abs() + 0.3 * vol_ratio + 0.3 * liq_z.abs()).fillna(0.0),
        'trend_regime_score': trend_strength.abs().fillna(0.0),
        'stress_regime_score': stress,
    }
