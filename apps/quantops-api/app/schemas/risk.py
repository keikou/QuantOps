from __future__ import annotations

from pydantic import BaseModel


class RiskSnapshotResponse(BaseModel):
    gross_exposure: float
    net_exposure: float
    leverage: float
    drawdown: float
    var_95: float | None = None
    var_1d: float | None = None
    stress_loss: float | None = None
    risk_limit: dict
    concentration: float | None = None
    kill_switch: str | None = None
    trading_state: str | None = None
    alert_state: str
    alert: str | None = None
    data_status: str = 'unknown'
    data_source: str = 'unknown'
    status_reason: str | None = None
    is_stale: bool = False
    as_of: str
