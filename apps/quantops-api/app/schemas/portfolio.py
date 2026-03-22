from __future__ import annotations

from pydantic import BaseModel


class PositionItem(BaseModel):
    symbol: str
    side: str | None = None
    weight: float
    notional: float
    pnl: float
    quantity: float | None = None
    avg_price: float | None = None
    mark_price: float | None = None
    strategy_id: str | None = None
    alpha_family: str | None = None
    price_source: str | None = None
    quote_time: str | None = None
    quote_age_sec: float | None = None
    stale: bool | None = None


class PortfolioOverviewResponse(BaseModel):
    portfolio_value: float
    total_equity: float | None = None
    balance: float | None = None
    cash: float
    free_cash: float | None = None
    free_margin: float | None = None
    used_margin: float | None = None
    unrealized: float | None = None
    collateral_equity: float | None = None
    available_margin: float | None = None
    margin_utilization: float | None = None
    pnl: float
    realized_pnl: float | None = None
    unrealized_pnl: float | None = None
    fees_paid: float | None = None
    drawdown: float
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    leverage: float
    expected_volatility: float | None = None
    expected_sharpe: float | None = None
    weights: dict[str, float]
    positions: list[PositionItem]
    quotes_as_of: str | None = None
    stale_positions: int | None = None
    as_of: str
