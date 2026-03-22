from __future__ import annotations


def classify_regime(features: dict[str, float]) -> str:
    trend = abs(features.get('trend_strength', 0.0))
    stress = features.get('stress_regime_score', 0.0)
    vol_ratio = features.get('volatility_ratio', 0.0)
    if stress > 1.7 or features.get('liquidation_spike', 0.0) > 2.0 or features.get('market_regime_score', 0.0) > 2.0:
        return 'panic'
    if trend > 0.015 and vol_ratio > 0.9:
        if features.get('momentum_4', 0.0) >= 0:
            return 'trend_up'
        return 'trend_down'
    return 'range'
