from __future__ import annotations

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    ok: bool = True
    message: str = "ok"


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "quantops-api"
    version: str


class ActionResponse(BaseModel):
    ok: bool = True
    action: str
    result: dict = Field(default_factory=dict)
