from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.territories.router import router as territories_router


def create_app() -> FastAPI:
    app = FastAPI(title="MADAVOLA API", version="v1")
    app.include_router(auth_router)
    app.include_router(territories_router)
    return app


app = create_app()
