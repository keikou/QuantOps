LAST_ATTRIBUTION = []

def build_attribution(forecasts: list[dict], targets: dict) -> list[dict]:
    global LAST_ATTRIBUTION
    out = []
    for f in forecasts:
        out.append({
            "strategy_id": f["strategy_id"],
            "symbol": f["symbol"],
            "expected_return": f["expected_return"],
            "confidence": f["confidence"],
            "target_weight": targets.get(f["symbol"], 0.0),
        })
    LAST_ATTRIBUTION = out
    return out

def latest_attribution():
    return LAST_ATTRIBUTION
