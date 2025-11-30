import structlog
from typing import Iterator

from psycopg import Connection

from app.repository.database import connection

logger = structlog.get_logger(__name__)

def get_connection() -> Iterator[Connection]:
    logger.debug("deps: acquiring db connection for request")
    with connection() as conn:
        yield conn
