import logging
import os
from pathlib import Path

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.repository.database import init_pool

logger = logging.getLogger(__name__)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE")


def configure_logging():
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if LOG_FILE:
        log_path = Path(LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="SuperScooters API")

    @app.on_event("startup")
    def _startup():
        logger.info("app: initializing database pool")
        init_pool()

    app.include_router(api_router)
    logger.info("app: router registered")
    return app


app = create_app()
