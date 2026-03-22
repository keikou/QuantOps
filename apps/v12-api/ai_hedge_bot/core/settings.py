from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    mode: str = os.getenv("AHB_MODE", "paper")
    symbols: list[str] = field(default_factory=lambda: [s.strip() for s in os.getenv("AHB_SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT,WLDUSDT,DOGEUSDT").split(",") if s.strip()])
    timeframe: str = os.getenv("AHB_TIMEFRAME", "15m")
    runtime_dir: Path = Path(os.getenv("AHB_RUNTIME_DIR", "runtime"))
    max_gross_exposure: float = float(os.getenv("AHB_MAX_GROSS_EXPOSURE", "1.0"))
    max_symbol_weight: float = float(os.getenv("AHB_MAX_SYMBOL_WEIGHT", "0.35"))
    family_weight_cap: float = float(os.getenv("AHB_FAMILY_WEIGHT_CAP", "0.50"))
    panic_gross_exposure: float = float(os.getenv("AHB_PANIC_GROSS_EXPOSURE", "0.50"))
    panic_symbol_weight: float = float(os.getenv("AHB_PANIC_SYMBOL_WEIGHT", "0.20"))
    nightly_update_min_evals: int = int(os.getenv("AHB_NIGHTLY_UPDATE_MIN_EVALS", "10"))
    use_live_market_data: bool = _bool("AHB_USE_LIVE_MARKET_DATA", False)
    price_source: str = os.getenv("AHB_PRICE_SOURCE", "binance_book_ticker").strip().lower()
    allow_synthetic_quote_fallback: bool = _bool("AHB_ALLOW_SYNTHETIC_QUOTE_FALLBACK", True)
    strict_live_quotes: bool = _bool("AHB_STRICT_LIVE_QUOTES", False)
    binance_rest_base_url: str = os.getenv("AHB_BINANCE_REST_BASE_URL", "https://api.binance.com").rstrip('/')
    quote_timeout_sec: float = float(os.getenv("AHB_QUOTE_TIMEOUT_SEC", "5"))
    expected_return_scale: float = float(os.getenv("AHB_EXPECTED_RETURN_SCALE", "0.025"))
    expected_return_cap: float = float(os.getenv("AHB_EXPECTED_RETURN_CAP", "0.02"))
    score_normalization_scale: float = float(os.getenv("AHB_SCORE_NORMALIZATION_SCALE", "8.0"))
    expected_sharpe_cap: float = float(os.getenv("AHB_EXPECTED_SHARPE_CAP", "10.0"))
    portfolio_sharpe_cap: float = float(os.getenv("AHB_PORTFOLIO_SHARPE_CAP", "10.0"))
    risk_aversion: float = float(os.getenv("AHB_RISK_AVERSION", "6.0"))
    turnover_cost_bps: float = float(os.getenv("AHB_TURNOVER_COST_BPS", "8"))
    confidence_floor: float = float(os.getenv("AHB_CONFIDENCE_FLOOR", "0.10"))
    shadow_cycle_interval_sec: int = int(os.getenv("AHB_SHADOW_CYCLE_INTERVAL_SEC", "60"))
    shadow_min_notional_usd: float = float(os.getenv("AHB_SHADOW_MIN_NOTIONAL_USD", "250"))
    shadow_max_participation_rate: float = float(os.getenv("AHB_SHADOW_MAX_PARTICIPATION_RATE", "0.20"))
    shadow_order_expiry_sec: int = int(os.getenv("AHB_SHADOW_ORDER_EXPIRY_SEC", "120"))
    shadow_latency_ms: float = float(os.getenv("AHB_SHADOW_LATENCY_MS", "250"))
    shadow_spread_bps: float = float(os.getenv("AHB_SHADOW_SPREAD_BPS", "4.0"))
    shadow_fee_bps: float = float(os.getenv("AHB_SHADOW_FEE_BPS", "3.5"))
    shadow_impact_bps_per_participation: float = float(os.getenv("AHB_SHADOW_IMPACT_BPS_PER_PARTICIPATION", "12.0"))

    @property
    def db_path(self) -> Path:
        return self.runtime_dir / 'analytics.duckdb'

    @property
    def log_dir(self) -> Path:
        return self.runtime_dir / 'logs'

    @property
    def weights_path(self) -> Path:
        return self.runtime_dir / 'alpha_weights.json'


SETTINGS = Settings()
SETTINGS.runtime_dir.mkdir(parents=True, exist_ok=True)
SETTINGS.log_dir.mkdir(parents=True, exist_ok=True)
