from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_alert_service
from app.services.alert_service import AlertService

router = APIRouter()


@router.get('')
async def list_alerts(service: AlertService = Depends(get_alert_service)) -> dict:
    service.evaluate_rules()
    return service.list_alerts()


@router.post('/{alert_id}/acknowledge')
async def acknowledge_alert(alert_id: str, service: AlertService = Depends(get_alert_service)) -> dict:
    result = service.acknowledge(alert_id)
    return {'ok': True, 'message': f'acknowledged {alert_id}', 'result': result}
