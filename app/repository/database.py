import os
import time
from contextlib import contextmanager
from typing import Iterator, Optional

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://superscooters:superscooters@localhost:5432/superscooters",
)

_pool: Optional[ConnectionPool] = None


def init_pool(**kwargs) -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=DATABASE_URL,
            kwargs=kwargs,
            open=False,
            min_size=int(os.getenv("DB_POOL_MIN_SIZE", 1)),
            max_size=int(os.getenv("DB_POOL_MAX_SIZE", 10)),
        )
        attempts = 0
        while True:
            try:
                _pool.open()
                break
            except Exception:
                attempts += 1
                if attempts >= 5:
                    raise
                time.sleep(1)
    return _pool


def get_pool() -> ConnectionPool:
    if _pool is None:
        raise RuntimeError("Connection pool is not initialized; call init_pool() first")
    return _pool


@contextmanager
def connection() -> Iterator[Connection]:
    pool = get_pool()
    with pool.connection() as conn:
        conn.execute("SET search_path TO public, partman")
        conn.row_factory = dict_row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
