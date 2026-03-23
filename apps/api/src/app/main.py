from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.config import settings
from app.db import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        initialize_database()
    yield


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.include_router(health_router)
    application.include_router(projects_router)
    return application


app = create_app()
