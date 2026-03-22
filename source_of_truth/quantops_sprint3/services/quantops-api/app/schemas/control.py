from __future__ import annotations

from pydantic import BaseModel


class StrategyActionRequest(BaseModel):
    strategy_id: str


class ControlActionResponse(BaseModel):
    ok: bool = True
    action: str
    target: str
    result: dict
