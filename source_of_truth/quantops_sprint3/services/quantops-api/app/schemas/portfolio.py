from __future__ import annotations

from pydantic import BaseModel


class PositionItem(BaseModel):
    symbol: str
    weight: float
    notional: float
    pnl: float


class PortfolioOverviewResponse(BaseModel):
    portfolio_value: float
    cash: float
    pnl: float
    drawdown: float
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    leverage: float
    weights: dict[str, float]
    positions: list[PositionItem]
    as_of: str
