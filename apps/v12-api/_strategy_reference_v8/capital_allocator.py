from src.strategy.strategy_registry import get_registry

def allocate_capital(forecasts: list[dict]) -> dict:
    reg = get_registry()
    alloc = {}
    for f in forecasts:
        st = f["strategy_id"]
        if not reg[st]["enabled"]:
            continue
        alloc[st] = {
            "capital_weight": reg[st]["capital_weight"],
            "risk_budget": reg[st]["risk_budget"],
            "score": round(f["expected_return"] * reg[st]["capital_weight"], 6),
        }
    return alloc
