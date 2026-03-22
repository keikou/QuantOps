from src.strategy.alpha_pipeline import build_alpha_signals
from src.strategy.signal_router import route_signals
from src.strategy.forecast_blender import blend_forecasts
from src.strategy.strategy_guard import guard_signal

LAST_SIGNALS = []
LAST_FORECASTS = []

def run_cycle():
    global LAST_SIGNALS, LAST_FORECASTS
    raw = build_alpha_signals()
    routed = route_signals(raw)
    forecasts = [f for f in blend_forecasts(routed) if guard_signal(f)]
    LAST_SIGNALS = routed
    LAST_FORECASTS = forecasts
    return {"raw_count": len(raw), "signal_count": len(routed), "forecast_count": len(forecasts)}

def latest_signals():
    return LAST_SIGNALS

def latest_forecasts():
    return LAST_FORECASTS
