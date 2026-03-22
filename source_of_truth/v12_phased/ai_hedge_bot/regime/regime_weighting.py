from __future__ import annotations

REGIME_MULTIPLIERS = {
    'trend_up': {'momentum': 1.20, 'mean_reversion': 0.85, 'derivatives': 1.0, 'event': 1.0, 'orderflow': 1.0, 'volatility': 1.05, 'statistical': 1.0},
    'trend_down': {'momentum': 1.20, 'mean_reversion': 0.85, 'derivatives': 1.0, 'event': 1.0, 'orderflow': 1.0, 'volatility': 1.05, 'statistical': 1.0},
    'range': {'momentum': 0.85, 'mean_reversion': 1.20, 'derivatives': 1.0, 'event': 0.95, 'orderflow': 1.0, 'volatility': 0.90, 'statistical': 1.05},
    'panic': {'momentum': 0.70, 'mean_reversion': 0.80, 'derivatives': 1.10, 'event': 1.15, 'orderflow': 1.0, 'volatility': 0.75, 'statistical': 0.90},
}
