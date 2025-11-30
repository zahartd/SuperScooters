from fastapi import FastAPI
import structlog

from app.api.routes import router as api_router
from app.repository.database import init_pool
from app.logging_config import configure_logging

logger = structlog.get_logger(__name__)

def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="SuperScooters API")

    @app.on_event("startup")
    def _startup():
        logger.info("Starting SuperScooters API", version="1.0.0",)
        init_pool()
        logger.info("Database connection pool initialized")

    @app.on_event("shutdown")
    def _shutdown():
        logger.info("Shutting down SuperScooters API")

    app.include_router(api_router)
    return app


app = create_app()
