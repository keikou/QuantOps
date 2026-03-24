from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request

from app.core.deps import get_portfolio_service
from app.schemas.portfolio import PortfolioMetricsResponse, PortfolioOverviewResponse
from app.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("/overview", response_model=PortfolioOverviewResponse)
async def portfolio_overview(request: Request, service: PortfolioService = Depends(get_portfolio_service)) -> PortfolioOverviewResponse:
    started = time.perf_counter()
    response = PortfolioOverviewResponse(**await service.get_overview())
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return response


@router.get("/debug/overview")
async def portfolio_overview_debug(request: Request, service: PortfolioService = Depends(get_portfolio_service)) -> dict:
    started = time.perf_counter()
    payload = await service.get_overview_debug()
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.get("/metrics", response_model=PortfolioMetricsResponse)
async def portfolio_metrics(request: Request, service: PortfolioService = Depends(get_portfolio_service)) -> PortfolioMetricsResponse:
    started = time.perf_counter()
    response = PortfolioMetricsResponse(**await service.get_metrics())
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return response


@router.get("/debug/metrics")
async def portfolio_metrics_debug(request: Request, service: PortfolioService = Depends(get_portfolio_service)) -> dict:
    started = time.perf_counter()
    payload = await service.get_metrics_debug()
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.get("/positions")
async def positions(request: Request, service: PortfolioService = Depends(get_portfolio_service)) -> list[dict]:
    started = time.perf_counter()
    payload = await service.get_positions()
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.get("/debug/positions")
async def positions_debug(request: Request, service: PortfolioService = Depends(get_portfolio_service)) -> dict:
    started = time.perf_counter()
    payload = await service.get_positions_debug()
    request.state.handler_duration_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return payload


@router.get("/exposure")
async def exposure(service: PortfolioService = Depends(get_portfolio_service)) -> dict:
    return await service.get_exposure()
