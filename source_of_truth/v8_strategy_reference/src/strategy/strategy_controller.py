from src.strategy.strategy_registry import get_registry, enable_strategy, disable_strategy, set_budget
from src.strategy.strategy_runtime import run_cycle, latest_signals, latest_forecasts
from src.strategy.capital_allocator import allocate_capital
from src.strategy.risk_budget_engine import apply_risk_budgets
from src.strategy.portfolio_engine import build_targets
from src.strategy.attribution_engine import build_attribution, latest_attribution

LAST_ALLOCATION = {}
LAST_BUDGETED = {}
LAST_TARGETS = {}

def status():
    return {
        "active_strategy_count": sum(1 for _, v in get_registry().items() if v["enabled"]),
        "total_strategy_count": len(get_registry()),
    }

def registry():
    return get_registry()

def run_strategy_cycle():
    global LAST_ALLOCATION, LAST_BUDGETED, LAST_TARGETS
    run_cycle()
    forecasts = latest_forecasts()
    alloc = allocate_capital(forecasts)
    budgeted = apply_risk_budgets(alloc)
    targets = build_targets(forecasts, budgeted)
    build_attribution(forecasts, targets["targets"])
    LAST_ALLOCATION = alloc
    LAST_BUDGETED = budgeted
    LAST_TARGETS = targets
    return {
        "signals": len(latest_signals()),
        "forecasts": len(forecasts),
        "strategies": len(alloc),
        "symbols": len(targets["targets"]),
    }

def signals():
    return latest_signals()

def targets():
    return LAST_TARGETS

def allocation():
    return {"raw_allocation": LAST_ALLOCATION, "budgeted_allocation": LAST_BUDGETED}

def attribution():
    return latest_attribution()

def enable(strategy_id: str):
    return enable_strategy(strategy_id)

def disable(strategy_id: str):
    return disable_strategy(strategy_id)

def set_strategy_budget(strategy_id: str, capital_weight: float, risk_budget: float):
    return set_budget(strategy_id, capital_weight, risk_budget)
