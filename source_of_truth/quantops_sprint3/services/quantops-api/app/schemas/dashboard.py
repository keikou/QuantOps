from __future__ import annotations

from pydantic import BaseModel


class DashboardOverviewResponse(BaseModel):
    portfolio_value: float
    pnl: float
    gross_exposure: float
    net_exposure: float
    leverage: float
    active_strategies: int
    alerts: list[dict]
    as_of: str


class SystemHealthResponse(BaseModel):
    status: str
    services: dict
    as_of: str
