from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_alert_service
from app.schemas.alerts import AlertActionRequest, AlertListResponse
from app.services.alert_service import AlertService

router = APIRouter()

@router.post('/evaluate')
def evaluate(service: AlertService = Depends(get_alert_service)) -> dict:
    return service.evaluate_rules()

@router.get('', response_model=AlertListResponse)
def list_alerts(service: AlertService = Depends(get_alert_service)) -> AlertListResponse:
    return AlertListResponse(**service.list_alerts())

@router.post('/acknowledge')
def acknowledge(payload: AlertActionRequest, service: AlertService = Depends(get_alert_service)) -> dict:
    return service.acknowledge(payload.alert_id, actor_id=payload.actor_id)

@router.post('/resolve')
def resolve(payload: AlertActionRequest, service: AlertService = Depends(get_alert_service)) -> dict:
    return service.resolve(payload.alert_id, actor_id=payload.actor_id)
