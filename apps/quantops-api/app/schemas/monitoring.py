from pydantic import BaseModel, Field

class MonitoringSystemResponse(BaseModel):
    status: str
    services: dict = Field(default_factory=dict)
    worker_status: str | None = None
    heartbeat_age_sec: float | None = None
    last_activity_as_of: str | None = None
    as_of: str

class MonitoringExecutionResponse(BaseModel):
    status: str
    execution: dict = Field(default_factory=dict)
    as_of: str

class MonitoringServicesResponse(BaseModel):
    items: list[dict] = Field(default_factory=list)
    as_of: str
