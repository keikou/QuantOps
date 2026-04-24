from __future__ import annotations

FEATURE_CATALOG = [
    "returns",
    "log_returns",
    "volume",
    "volatility",
    "high_low_range",
    "close_open_return",
    "orderflow_imbalance",
    "spread_bps",
    "funding_rate",
    "open_interest",
]

UNARY_OPERATORS = ["neg", "abs", "log1p_abs", "sqrt_abs", "zscore", "winsorize"]
BINARY_OPERATORS = ["add", "sub", "mul", "div_safe", "max", "min"]
TIME_SERIES_OPERATORS = ["ts_mean", "ts_std", "ts_rank", "ts_delta", "ts_zscore"]
CROSS_SECTIONAL_OPERATORS = ["rank", "normalize", "cs_zscore"]
WINDOW_CHOICES = [3, 5, 10, 20, 30, 60, 120]

