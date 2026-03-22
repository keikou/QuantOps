from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_portfolio_service
from app.schemas.portfolio import PortfolioOverviewResponse
from app.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("/overview", response_model=PortfolioOverviewResponse)
async def portfolio_overview(service: PortfolioService = Depends(get_portfolio_service)) -> PortfolioOverviewResponse:
    return PortfolioOverviewResponse(**await service.get_overview())


@router.get("/positions")
async def positions(service: PortfolioService = Depends(get_portfolio_service)) -> list[dict]:
    return await service.get_positions()


@router.get("/exposure")
async def exposure(service: PortfolioService = Depends(get_portfolio_service)) -> dict:
    return await service.get_exposure()
