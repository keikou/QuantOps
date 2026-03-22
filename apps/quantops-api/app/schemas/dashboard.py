from __future__ import annotations

from pydantic import BaseModel


class DashboardOverviewResponse(BaseModel):
    portfolio_value: float
    total_equity: float | None = None
    balance: float | None = None
    used_margin: float | None = None
    free_margin: float | None = None
    unrealized: float | None = None
    pnl: float
    gross_exposure: float
    net_exposure: float
    leverage: float
    active_strategies: int
    alerts: list[dict]
    open_alerts: int = 0
    running_jobs: int = 0
    mock_mode: bool | None = None
    latest_run_id: str | None = None
    latest_execution_timestamp: str | None = None
    as_of: str


class SystemHealthResponse(BaseModel):
    status: str
    services: dict
    as_of: str
