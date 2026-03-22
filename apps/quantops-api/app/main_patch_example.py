from fastapi import FastAPI

from app.api.routes.modes import router as modes_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.acceptance import router as acceptance_router
from app.api.routes.scheduler_sprint5d import router as scheduler_sprint5d_router


def mount_sprint5d_routes(app: FastAPI) -> None:
    app.include_router(modes_router)
    app.include_router(incidents_router)
    app.include_router(acceptance_router)
    app.include_router(scheduler_sprint5d_router)
