from typing import Optional

from psycopg import Connection

from app.models import OrderData

import structlog
logger = structlog.get_logger(__name__)

def insert_order(conn: Connection, order: OrderData) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO orders (
                id, user_id, scooter_id, zone_id,
                price_per_minute, price_unlock, deposit,
                total_amount, start_time, finish_time, created_at
            )
            VALUES (
                %(id)s, %(user_id)s, %(scooter_id)s, %(zone_id)s,
                %(price_per_minute)s, %(price_unlock)s, %(deposit)s,
                %(total_amount)s, %(start_time)s, %(finish_time)s, %(start_time)s
            )
            """,
            {
                "id": order.id,
                "user_id": order.user_id,
                "scooter_id": order.scooter_id,
                "zone_id": getattr(order, "zone_id", ""),
                "price_per_minute": order.price_per_minute,
                "price_unlock": order.price_unlock,
                "deposit": order.deposit,
                "total_amount": order.total_amount,
                "start_time": order.start_time,
                "finish_time": order.finish_time,
            },
        )
    logger.debug("orders_repo: inserted order", order_id=order.id, user_id=order.user_id)


def get_order(conn: Connection, order_id: str) -> Optional[OrderData]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM orders WHERE id = %(order_id)s",
            {"order_id": order_id},
        )
        result = cur.fetchone()
    if not result:
        logger.debug("orders_repo: order not found", order_id=order_id)
        return None
    logger.debug("orders_repo: fetched order", order_id=order_id)
    return OrderData(
        id=str(result["id"]),
        user_id=str(result["user_id"]),
        scooter_id=str(result["scooter_id"]),
        zone_id=str(result["zone_id"]),
        price_per_minute=int(result["price_per_minute"]),
        price_unlock=int(result["price_unlock"]),
        deposit=int(result["deposit"]),
        total_amount=int(result["total_amount"]),
        start_time=result["start_time"],
        finish_time=result["finish_time"],
    )


def update_order_finish(conn: Connection, order: OrderData) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE orders
            SET finish_time = %(finish_time)s,
                total_amount = %(total_amount)s
            WHERE id = %(id)s
            """,
            {
                "finish_time": order.finish_time,
                "total_amount": order.total_amount,
                "id": order.id,
            },
        )
    logger.debug(
        "orders_repo: updated finish",
        order_id=order.id,
        total_amount=order.total_amount
    )
