from __future__ import annotations

from pydantic import BaseModel, Field


class AllocationRequest(BaseModel):
    total_capital: float | None = Field(default=None, description="Optional capital base for allocation")


class StrategyRuntimeRequest(BaseModel):
    strategy_id: str


class RuntimeStatusRequest(BaseModel):
    strategy_id: str
    desired_state: str
