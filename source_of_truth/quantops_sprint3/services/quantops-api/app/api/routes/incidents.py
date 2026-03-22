from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_incident_service
from app.schemas.incidents import IncidentCreateRequest, IncidentResolveRequest
from app.services.incident_service import IncidentService

router = APIRouter()

@router.get('')
def list_incidents(service: IncidentService = Depends(get_incident_service)) -> dict:
    return service.list_incidents()

@router.post('/create')
def create_incident(payload: IncidentCreateRequest, service: IncidentService = Depends(get_incident_service)) -> dict:
    return service.create_incident(payload.model_dump())

@router.post('/resolve')
def resolve_incident(payload: IncidentResolveRequest, service: IncidentService = Depends(get_incident_service)) -> dict:
    return service.resolve(payload.incident_id, note=payload.note)
