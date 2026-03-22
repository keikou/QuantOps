def apply_risk_budgets(allocation: dict) -> dict:
    out = {}
    for strategy_id, row in allocation.items():
        capped_score = max(min(row["score"], row["risk_budget"]), -row["risk_budget"])
        out[strategy_id] = {
            **row,
            "budgeted_score": round(capped_score, 6),
        }
    return out
