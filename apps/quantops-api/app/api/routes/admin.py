from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_admin_service, get_frontend_telemetry_service
from app.services.admin_service import AdminService
from app.services.frontend_telemetry_service import FrontendTelemetryService

router = APIRouter()

@router.get('/audit-logs')
def audit_logs(service: AdminService = Depends(get_admin_service)) -> dict:
    return service.get_audit_logs()

@router.get('/operator-actions')
def operator_actions(service: AdminService = Depends(get_admin_service)) -> dict:
    return service.get_operator_actions()

@router.get('/config-changes')
def config_changes(service: AdminService = Depends(get_admin_service)) -> dict:
    return service.get_config_changes()

@router.get('/mode-switches')
def mode_switches(service: AdminService = Depends(get_admin_service)) -> dict:
    return service.get_mode_switches()


@router.post('/frontend-events')
def frontend_events(payload: dict, service: FrontendTelemetryService = Depends(get_frontend_telemetry_service)) -> dict:
    return service.record_event(payload)
