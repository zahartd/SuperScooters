import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://superscooters:superscooters@localhost:5432/superscooters",
)

# Lazily created pool; apps can initialize early via init_pool().
_pool: Optional[AsyncConnectionPool] = None


def init_pool(**kwargs) -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            conninfo=DATABASE_URL,
            kwargs=kwargs,
            open=False,
            min_size=int(os.getenv("DB_POOL_MIN_SIZE", 1)),
            max_size=int(os.getenv("DB_POOL_MAX_SIZE", 10)),
        )
        _pool.open(wait=True)
    return _pool


def get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("Connection pool is not initialized; call init_pool() first")
    return _pool


@asynccontextmanager
async def connection() -> AsyncIterator[AsyncConnection]:
    pool = get_pool()
    async with pool.connection() as conn:
        await conn.set_autocommit(False)
        conn.row_factory = dict_row
        try:
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
