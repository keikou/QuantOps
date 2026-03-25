from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request, WebSocket

from app.core.deps import get_command_center_service, get_event_stream_service
from app.schemas.command_center import (
    CommandCenterAuditSummaryResponse,
    CommandCenterHardeningStatusResponse,
    CommandCenterActionResponse,
    CommandCenterExecutionLatestResponse,
    CommandCenterOverviewResponse,
    CommandCenterPortfolioSummaryResponse,
    CommandCenterRiskActionRequest,
    CommandCenterRuntimeIssueAcknowledgeRequest,
    CommandCenterRuntimeRunReviewRequest,
    CommandCenterRiskSummaryResponse,
    CommandCenterStrategiesResponse,
    CommandCenterStrategyActionRequest,
    CommandCenterStrategyRiskUpdateRequest,
    CommandCenterSystemSummaryResponse,
)
from app.services.command_center_service import CommandCenterService
from app.services.event_stream_service import EventStreamService
from app.security.rbac import RequestActor, get_request_actor, require_role

router = APIRouter()


@router.get('/overview', response_model=CommandCenterOverviewResponse)
async def overview(service: CommandCenterService = Depends(get_command_center_service)) -> CommandCenterOverviewResponse:
    return CommandCenterOverviewResponse(**await service.get_overview())


@router.get('/strategies', response_model=CommandCenterStrategiesResponse)
async def strategies(service: CommandCenterService = Depends(get_command_center_service)) -> CommandCenterStrategiesResponse:
    return CommandCenterStrategiesResponse(**await service.get_strategies())


@router.get('/execution/latest', response_model=CommandCenterExecutionLatestResponse)
async def execution_latest(service: CommandCenterService = Depends(get_command_center_service)) -> CommandCenterExecutionLatestResponse:
    return CommandCenterExecutionLatestResponse(**await service.get_execution_latest())


@router.get('/runtime/latest')
async def runtime_latest(service: CommandCenterService = Depends(get_command_center_service)) -> dict:
    return await service.get_runtime_latest()


@router.get('/runtime/runs')
async def runtime_runs(
    request: Request,
    limit: int = 20,
    window_minutes: int = 5,
    operator_state: str | None = None,
    bridge_state: str | None = None,
    issue_code: str | None = None,
    reason_code: str | None = None,
    blocking_component: str | None = None,
    degraded: bool | None = None,
    event_chain_complete: bool | None = None,
    artifact_available: bool | None = None,
    service: CommandCenterService = Depends(get_command_center_service),
) -> dict:
    started = time.perf_counter()
    payload = await service.get_runtime_runs(
        limit=limit,
        window_minutes=window_minutes,
        operator_state=operator_state,
        bridge_state=bridge_state,
        issue_code=issue_code,
        reason_code=reason_code,
        blocking_component=blocking_component,
        degraded=degraded,
        event_chain_complete=event_chain_complete,
        artifact_available=artifact_available,
    )
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.get('/runtime/issues')
async def runtime_issues(
    request: Request,
    limit: int = 25,
    window_minutes: int = 5,
    service: CommandCenterService = Depends(get_command_center_service),
) -> dict:
    started = time.perf_counter()
    payload = await service.get_runtime_issues(limit=limit, window_minutes=window_minutes)
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.post('/runtime/runs/{run_id}/review', response_model=CommandCenterActionResponse)
async def review_runtime_run(
    run_id: str,
    payload: CommandCenterRuntimeRunReviewRequest,
    actor: RequestActor = Depends(get_request_actor),
    service: CommandCenterService = Depends(get_command_center_service),
) -> CommandCenterActionResponse:
    require_role(actor, 'operator')
    return CommandCenterActionResponse(
        **await service.review_runtime_run(
            run_id=run_id,
            review_status=payload.review_status,
            acknowledged=payload.acknowledged,
            operator_note=payload.operator_note,
            actor=actor,
        )
    )


@router.post('/runtime/issues/{diagnosis_code}/acknowledge', response_model=CommandCenterActionResponse)
async def acknowledge_runtime_issue(
    diagnosis_code: str,
    payload: CommandCenterRuntimeIssueAcknowledgeRequest,
    actor: RequestActor = Depends(get_request_actor),
    service: CommandCenterService = Depends(get_command_center_service),
) -> CommandCenterActionResponse:
    require_role(actor, 'operator')
    return CommandCenterActionResponse(
        **await service.acknowledge_runtime_issue(
            diagnosis_code=diagnosis_code,
            note=payload.note,
            actor=actor,
        )
    )


@router.get('/debug/execution')
async def execution_debug(request: Request, service: CommandCenterService = Depends(get_command_center_service)) -> dict:
    started = time.perf_counter()
    payload = await service.get_execution_debug()
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.get('/debug/runtime')
async def runtime_debug(request: Request, run_id: str | None = None, service: CommandCenterService = Depends(get_command_center_service)) -> dict:
    started = time.perf_counter()
    payload = await service.get_runtime_debug(run_id=run_id)
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.get('/portfolio/summary', response_model=CommandCenterPortfolioSummaryResponse)
async def portfolio_summary(service: CommandCenterService = Depends(get_command_center_service)) -> CommandCenterPortfolioSummaryResponse:
    return CommandCenterPortfolioSummaryResponse(**await service.get_portfolio_summary())


@router.get('/risk/summary', response_model=CommandCenterRiskSummaryResponse)
async def risk_summary(service: CommandCenterService = Depends(get_command_center_service)) -> CommandCenterRiskSummaryResponse:
    return CommandCenterRiskSummaryResponse(**await service.get_risk_summary())


@router.get('/system/summary', response_model=CommandCenterSystemSummaryResponse)
async def system_summary(service: CommandCenterService = Depends(get_command_center_service)) -> CommandCenterSystemSummaryResponse:
    return CommandCenterSystemSummaryResponse(**await service.get_system_summary())


@router.get('/system/jobs')
def system_jobs(service: CommandCenterService = Depends(get_command_center_service)) -> dict:
    return service.get_system_jobs()


@router.get('/system/alerts')
def system_alerts(service: CommandCenterService = Depends(get_command_center_service)) -> dict:
    return service.get_system_alerts()



@router.post('/strategies/start', response_model=CommandCenterActionResponse)
async def start_strategy(
    payload: CommandCenterStrategyActionRequest,
    actor: RequestActor = Depends(get_request_actor),
    service: CommandCenterService = Depends(get_command_center_service),
) -> CommandCenterActionResponse:
    require_role(actor, 'operator')
    return CommandCenterActionResponse(**await service.start_strategy(payload.strategy_id))


@router.post('/strategies/stop', response_model=CommandCenterActionResponse)
async def stop_strategy(
    payload: CommandCenterStrategyActionRequest,
    actor: RequestActor = Depends(get_request_actor),
    service: CommandCenterService = Depends(get_command_center_service),
) -> CommandCenterActionResponse:
    require_role(actor, 'operator')
    return CommandCenterActionResponse(**await service.stop_strategy(payload.strategy_id))


@router.post('/strategies/risk', response_model=CommandCenterActionResponse)
async def update_strategy_risk(
    payload: CommandCenterStrategyRiskUpdateRequest,
    actor: RequestActor = Depends(get_request_actor),
    service: CommandCenterService = Depends(get_command_center_service),
) -> CommandCenterActionResponse:
    require_role(actor, 'operator')
    return CommandCenterActionResponse(**await service.update_strategy_risk(payload.strategy_id, payload.risk_budget, payload.note))


@router.post('/risk/pause', response_model=CommandCenterActionResponse)
async def pause_risk(
    payload: CommandCenterRiskActionRequest,
    actor: RequestActor = Depends(get_request_actor),
    service: CommandCenterService = Depends(get_command_center_service),
) -> CommandCenterActionResponse:
    require_role(actor, 'risk_manager')
    return CommandCenterActionResponse(**await service.pause_risk(payload.note))


@router.post('/risk/resume', response_model=CommandCenterActionResponse)
async def resume_risk(
    payload: CommandCenterRiskActionRequest,
    actor: RequestActor = Depends(get_request_actor),
    service: CommandCenterService = Depends(get_command_center_service),
) -> CommandCenterActionResponse:
    require_role(actor, 'risk_manager')
    return CommandCenterActionResponse(**await service.resume_risk(payload.note))


@router.post('/risk/kill-switch', response_model=CommandCenterActionResponse)
async def kill_switch(
    payload: CommandCenterRiskActionRequest,
    actor: RequestActor = Depends(get_request_actor),
    service: CommandCenterService = Depends(get_command_center_service),
) -> CommandCenterActionResponse:
    require_role(actor, 'admin')
    return CommandCenterActionResponse(**await service.kill_switch(payload.note))


@router.websocket('/ws/events')
async def command_center_events(
    websocket: WebSocket,
    service: EventStreamService = Depends(get_event_stream_service),
) -> None:
    await service.stream(websocket)


@router.get('/hardening/status', response_model=CommandCenterHardeningStatusResponse)
async def hardening_status(
    actor: RequestActor = Depends(get_request_actor),
    service: CommandCenterService = Depends(get_command_center_service),
) -> CommandCenterHardeningStatusResponse:
    require_role(actor, 'viewer')
    return CommandCenterHardeningStatusResponse(**service.get_hardening_status())


@router.get('/audit/summary', response_model=CommandCenterAuditSummaryResponse)
async def audit_summary(
    actor: RequestActor = Depends(get_request_actor),
    service: CommandCenterService = Depends(get_command_center_service),
) -> CommandCenterAuditSummaryResponse:
    require_role(actor, 'admin')
    return CommandCenterAuditSummaryResponse(**service.get_audit_summary())
