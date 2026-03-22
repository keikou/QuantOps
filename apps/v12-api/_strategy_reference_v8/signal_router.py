def route_signals(raw_signals: list[dict]) -> list[dict]:
    out = []
    for s in raw_signals:
        out.append({
            "strategy_id": s["strategy_id"],
            "symbol": s["symbol"],
            "normalized_score": round(float(s["raw_score"]), 6),
            "confidence": float(s["confidence"]),
            "horizon": s["horizon"],
        })
    return out
