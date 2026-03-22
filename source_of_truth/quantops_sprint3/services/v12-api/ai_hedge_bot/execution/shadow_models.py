from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

OrderState = Literal["created", "pending", "partial", "filled", "cancelled", "expired"]
OrderType = Literal["market", "limit"]
MakerTaker = Literal["maker", "taker"]
LiquidityBucket = Literal["deep", "medium", "thin"]


@dataclass
class ExecutionIntent:
    decision_id: str
    portfolio_id: str
    signal_id: str
    symbol: str
    side: str
    target_weight: float
    target_notional_usd: float
    urgency: str
    max_slice: float
    decision_ts: datetime
    market_snapshot_ts: datetime


@dataclass
class ShadowOrder:
    shadow_order_id: str
    decision_id: str
    portfolio_id: str
    signal_id: str
    symbol: str
    side: str
    venue: str
    order_type: OrderType
    tif: str
    qty: float
    arrival_mid_price: float
    limit_price: float
    created_ts: datetime
    status: OrderState
    urgency: str
    participation_rate: float


@dataclass
class ShadowFill:
    fill_id: str
    shadow_order_id: str
    portfolio_id: str
    signal_id: str
    symbol: str
    side: str
    fill_ts: datetime
    fill_qty: float
    fill_price: float
    maker_taker: MakerTaker
    fee_usd: float
    fee_bps: float
    liquidity_bucket: LiquidityBucket


@dataclass
class ExecutionCostBreakdown:
    cost_id: str
    shadow_order_id: str
    portfolio_id: str
    signal_id: str
    symbol: str
    side: str
    spread_cost_bps: float
    slippage_bps: float
    latency_cost_bps: float
    impact_cost_bps: float
    fee_bps: float
    total_cost_bps: float
    arrival_mid_price: float
    effective_fill_price: float
    timestamp: datetime


@dataclass
class LatencySnapshot:
    snapshot_id: str
    shadow_order_id: str
    portfolio_id: str
    symbol: str
    decision_to_order_ms: float
    order_to_first_fill_ms: float
    order_to_complete_ms: float
    timestamp: datetime


@dataclass
class ShadowPnLSnapshot:
    snapshot_id: str
    portfolio_id: str
    symbol: str
    side: str
    gross_alpha_pnl_usd: float
    net_shadow_pnl_usd: float
    execution_drag_usd: float
    slippage_drag_usd: float
    fee_drag_usd: float
    latency_drag_usd: float
    timestamp: datetime
