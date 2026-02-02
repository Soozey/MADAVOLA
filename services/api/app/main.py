from fastapi import FastAPI

from app.actors.router import router as actors_router
from app.auth.router import router as auth_router
from app.geopoints.router import router as geopoints_router
from app.health.router import router as health_router
from app.payments.router import router as payments_router
from app.territories.router import router as territories_router


def create_app() -> FastAPI:
    app = FastAPI(title="MADAVOLA API", version="v1")
    app.include_router(auth_router)
    app.include_router(actors_router)
    app.include_router(geopoints_router)
    app.include_router(health_router)
    app.include_router(payments_router)
    app.include_router(territories_router)
    return app


app = create_app()
