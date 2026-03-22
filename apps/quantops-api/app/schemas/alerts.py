from pydantic import BaseModel, Field

class AlertActionRequest(BaseModel):
    alert_id: str
    actor_id: str = "operator"

class AlertListResponse(BaseModel):
    count: int
    items: list[dict] = Field(default_factory=list)
