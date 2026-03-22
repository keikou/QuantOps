from pydantic import BaseModel

class IncidentCreateRequest(BaseModel):
    incident_type: str
    severity: str
    title: str
    description: str | None = None

class IncidentResolveRequest(BaseModel):
    incident_id: str
    note: str | None = None
