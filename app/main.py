from fastapi import FastAPI

from app.api.routes import router as api_router
from app.repository.database import init_pool


def create_app() -> FastAPI:
    app = FastAPI(title="SuperScooters API")

    @app.on_event("startup")
    def _startup():
        init_pool()

    app.include_router(api_router)
    return app


app = create_app()
