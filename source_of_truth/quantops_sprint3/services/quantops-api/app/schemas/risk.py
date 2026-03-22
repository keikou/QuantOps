from __future__ import annotations

from pydantic import BaseModel


class RiskSnapshotResponse(BaseModel):
    gross_exposure: float
    net_exposure: float
    leverage: float
    drawdown: float
    var_95: float | None = None
    stress_loss: float | None = None
    risk_limit: dict
    alert_state: str
    as_of: str
