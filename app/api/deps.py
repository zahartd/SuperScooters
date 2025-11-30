import logging
from typing import Iterator

from psycopg import Connection

from app.repository.database import connection

logger = logging.getLogger(__name__)


def get_connection() -> Iterator[Connection]:
    logger.debug("deps: acquiring db connection for request")
    with connection() as conn:
        yield conn
