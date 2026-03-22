from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_approval_service
from app.schemas.approval import ApprovalCreateRequest, ApprovalDecisionRequest
from app.services.approval_service import ApprovalService

router = APIRouter()

@router.get('/requests')
def list_requests(service: ApprovalService = Depends(get_approval_service)) -> dict:
    return service.list_requests()

@router.post('/request')
def create_request(payload: ApprovalCreateRequest, service: ApprovalService = Depends(get_approval_service)) -> dict:
    return service.create_request(payload.model_dump())

@router.post('/approve')
def approve(payload: ApprovalDecisionRequest, service: ApprovalService = Depends(get_approval_service)) -> dict:
    return service.approve(payload.request_id, actor_id=payload.actor_id, note=payload.note)

@router.post('/reject')
def reject(payload: ApprovalDecisionRequest, service: ApprovalService = Depends(get_approval_service)) -> dict:
    return service.reject(payload.request_id, actor_id=payload.actor_id, note=payload.note)
