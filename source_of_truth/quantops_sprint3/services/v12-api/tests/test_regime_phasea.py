from ai_hedge_bot.regime.regime_classifier import classify_regime


def test_phasea_regime_panic_detection():
    regime = classify_regime({'trend_strength': 0.0, 'volatility_ratio': 2.1, 'market_regime_score': 2.3})
    assert regime == 'panic'
