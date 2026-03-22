from ai_hedge_bot.regime.regime_classifier import classify_regime


def test_regime_classifier_returns_known_state():
    features = {'trend_strength': 0.02, 'stress_regime_score': 0.5, 'volatility_ratio': 1.2, 'momentum_4': 0.01, 'liquidation_spike': 0.0}
    assert classify_regime(features) in {'trend_up','trend_down','range','panic'}


def test_regime_classifier_detects_panic():
    features = {'trend_strength': 0.0, 'stress_regime_score': 2.0, 'volatility_ratio': 2.0, 'momentum_4': -0.01, 'liquidation_spike': 3.0}
    assert classify_regime(features) == 'panic'
