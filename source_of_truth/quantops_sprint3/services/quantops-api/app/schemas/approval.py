from pydantic import BaseModel, Field

class ApprovalCreateRequest(BaseModel):
    request_type: str
    target_id: str
    requested_by: str = "operator"
    summary: dict = Field(default_factory=dict)

class ApprovalDecisionRequest(BaseModel):
    request_id: str
    actor_id: str = "operator"
    note: str | None = None
