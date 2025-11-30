from fastapi import FastAPI
import structlog

from app.api.routes import router as api_router
from app.repository.database import init_pool
from app.logging_config import configure_logging
from app.metrics import MetricsMiddleware, start_metrics_server

logger = structlog.get_logger(__name__)

def create_app() -> FastAPI:
    configure_logging(
        log_level="INFO",
        log_file="app.log"
    )
    app = FastAPI(title="SuperScooters API")

    @app.on_event("startup")
    def _startup():
        logger.info("app: initializing database pool")
        init_pool()
        logger.info("Database connection pool initialized")

    @app.on_event("shutdown")
    def _shutdown():
        logger.info("Shutting down SuperScooters API")

    app.include_router(api_router)
    return app


app = create_app()
app.add_middleware(MetricsMiddleware)
start_metrics_server(8001)