REGISTRY = {
    "trend_core": {"enabled": True, "priority": 1, "capital_weight": 0.45, "risk_budget": 0.40, "health": "green"},
    "mean_reversion_core": {"enabled": True, "priority": 2, "capital_weight": 0.30, "risk_budget": 0.30, "health": "green"},
    "event_core": {"enabled": True, "priority": 3, "capital_weight": 0.25, "risk_budget": 0.30, "health": "green"},
}

def get_registry():
    return REGISTRY

def enable_strategy(strategy_id: str):
    REGISTRY[strategy_id]["enabled"] = True
    return REGISTRY[strategy_id]

def disable_strategy(strategy_id: str):
    REGISTRY[strategy_id]["enabled"] = False
    return REGISTRY[strategy_id]

def set_budget(strategy_id: str, capital_weight: float, risk_budget: float):
    REGISTRY[strategy_id]["capital_weight"] = capital_weight
    REGISTRY[strategy_id]["risk_budget"] = risk_budget
    return REGISTRY[strategy_id]
