from pydantic import BaseModel, Field

class RollbackRequest(BaseModel):
    strategy_id: str

class GovernanceListResponse(BaseModel):
    items: list[dict] = Field(default_factory=list)
    as_of: str | None = None
