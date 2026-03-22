def build_alpha_signals():
    return [
        {"strategy_id": "trend_core", "symbol": "BTCUSDT", "raw_score": 0.72, "confidence": 0.83, "horizon": "4h"},
        {"strategy_id": "mean_reversion_core", "symbol": "ETHUSDT", "raw_score": -0.36, "confidence": 0.71, "horizon": "1h"},
        {"strategy_id": "event_core", "symbol": "WLDUSDT", "raw_score": 0.51, "confidence": 0.68, "horizon": "30m"},
    ]
