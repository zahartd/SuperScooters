from typing import Iterator

from psycopg import Connection

from app.repository.database import connection


def get_connection() -> Iterator[Connection]:
    with connection() as conn:
        yield conn
