from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Literal

Side = Literal["long", "short", "neutral"]


@dataclass
class MarketSnapshot:
    symbol: str
    timestamp: datetime
    timeframe: str
    frame: Any


@dataclass
class AlphaMetadata:
    alpha_name: str
    alpha_family: str
    factor_type: str
    primary_horizon: str
    turnover_profile: str
    required_features: list[str]


@dataclass
class AlphaResult:
    metadata: AlphaMetadata
    direction: Side
    score: float
    confidence: float
    rationale: str


@dataclass
class Signal:
    signal_id: str
    symbol: str
    timestamp: datetime
    side: Side
    entry: float
    stop: float
    target: float
    net_score: float
    confidence: float
    dominant_alpha: str
    dominant_alpha_family: str
    signal_horizon: str
    signal_factor_type: str
    signal_signature: str
    portfolio_dedup_status: str = 'pending'
    alpha_results: list[AlphaResult] = field(default_factory=list)


@dataclass
class PortfolioIntent:
    symbol: str
    side: Side
    target_weight: float
    signal_id: str
    net_score: float


@dataclass
class ExpectedReturnEstimate:
    signal_id: str
    symbol: str
    side: Side
    expected_return_gross: float
    expected_return_net: float
    expected_volatility: float
    expected_sharpe: float
    turnover_penalty: float
    cost_penalty: float
    confidence_adjusted_score: float
    timestamp: datetime


@dataclass
class PortfolioWeight:
    portfolio_id: str
    signal_id: str
    symbol: str
    side: Side
    target_weight: float
    expected_return_net: float
    expected_volatility: float
    marginal_risk: float
    timestamp: datetime


@dataclass
class PortfolioAllocation:
    portfolio_id: str
    signal_id: str
    symbol: str
    side: Side
    target_weight: float
    notional_usd: float
    expected_pnl_usd: float
    expected_return_net: float
    timestamp: datetime


@dataclass
class PortfolioRiskSnapshot:
    portfolio_id: str
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    turnover_estimate: float
    portfolio_expected_return: float
    portfolio_expected_volatility: float
    portfolio_expected_sharpe: float
    concentration_top_weight: float
    timestamp: datetime


@dataclass
class Fill:
    signal_id: str
    symbol: str
    side: Side
    fill_price: float
    quantity: float
    timestamp: datetime


@dataclass
class PositionState:
    symbol: str
    side: Side
    quantity: float
    avg_price: float
    mark_price: float
    unrealized_pnl: float


@dataclass
class EvaluationResult:
    signal_id: str
    symbol: str
    side: Side
    horizon_1h_return: float
    horizon_4h_return: float
    mfe: float
    mae: float
    hit: bool


def to_dict(obj: Any) -> dict[str, Any]:
    return asdict(obj)
