from __future__ import annotations

from fastapi import FastAPI
from ai_hedge_bot.app.startup import lifespan
from ai_hedge_bot.api.routes import (
    system,
    market,
    signals,
    portfolio,
    orchestrator,
    execution,
    analytics,
    dashboard,
    strategy,
    research_factory,
    alpha,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title='AI Hedge Bot V12 PhaseH Sprint4',
        version='0.12.0-phaseh-sprint4',
        lifespan=lifespan,
    )
    for router in (
        system.router,
        market.router,
        signals.router,
        portfolio.router,
        orchestrator.router,
        execution.router,
        analytics.router,
        dashboard.router,
        strategy.router,
        research_factory.router,
        alpha.router,
    ):
        app.include_router(router)
    return app


app = create_app()
