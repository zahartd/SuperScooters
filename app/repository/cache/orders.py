import structlog
from psycopg import Connection

from app.models import OrderData
from app.repository.db import orders as orders_db
from app.utils.cache import ThreadSafeTTLCache


logger = structlog.get_logger(__name__)

_ORDER_CACHE_TTL_SECONDS = 2 * 60 * 60  # keep active orders + short tail
_ORDER_CACHE_MAXSIZE = 150_000

_order_cache: ThreadSafeTTLCache[str, OrderData] = ThreadSafeTTLCache(
    maxsize=_ORDER_CACHE_MAXSIZE,
    ttl=_ORDER_CACHE_TTL_SECONDS,
)


def _cache_order(order: OrderData) -> None:
    _order_cache.set(order.id, order)


def get_order(conn: Connection, order_id: str) -> OrderData | None:
    cached = _order_cache.get(order_id)
    if cached is not None:
        logger.debug("orders_cache: cache hit", order_id=order_id)
        return cached

    logger.debug("orders_cache: cache miss, reading db", order_id=order_id)
    order = orders_db.get_order(conn, order_id)
    if order:
        _cache_order(order)
    return order


def insert_order(conn: Connection, order: OrderData) -> None:
    orders_db.insert_order(conn, order)
    _cache_order(order)


def update_order_finish(conn: Connection, order: OrderData) -> None:
    orders_db.update_order_finish(conn, order)
    _cache_order(order)
