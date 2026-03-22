def blend_forecasts(signals: list[dict]) -> list[dict]:
    out = []
    for s in signals:
        out.append({
            "strategy_id": s["strategy_id"],
            "symbol": s["symbol"],
            "expected_return": round(s["normalized_score"] * s["confidence"], 6),
            "confidence": s["confidence"],
            "horizon": s["horizon"],
        })
    return out
