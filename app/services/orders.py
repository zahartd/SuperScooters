import uuid
from datetime import datetime, timezone
from typing import Optional

from psycopg import Connection

from app.clients import data_requests as dr
from app.models import OfferData, OrderData
from app.repository import orders as orders_repo
from app.utils.pricing import validate_pricing_token

MAGIC_CONSTANT2 = 5


def start_order(offer: OfferData, pricing_token: str, conn: Connection) -> OrderData:
    configs = dr.get_configs()
    validate_pricing_token(offer, pricing_token, configs)

    order = OrderData(
        str(uuid.uuid4()),
        user_id=offer.user_id,
        scooter_id=offer.scooter_id,
        zone_id=offer.zone_id,
        price_per_minute=offer.price_per_minute,
        price_unlock=offer.price_unlock,
        deposit=offer.deposit,
        total_amount=0,
        start_time=datetime.now(timezone.utc),
        finish_time=None,
    )

    dr.hold_money_for_order(offer.user_id, order.id, offer.deposit)
    orders_repo.insert_order(conn, order)
    return order


def finish_order(order_id: str, conn: Connection) -> OrderData:
    order = orders_repo.get_order(conn, order_id)
    if order is None:
        raise KeyError(order_id)

    order.finish_time = datetime.now(timezone.utc)
    if (order.finish_time - order.start_time).total_seconds() < MAGIC_CONSTANT2:
        dr.clear_money_for_order(order.user_id, order_id, 0)
    else:
        order.total_amount = (
            int((order.finish_time - order.start_time).total_seconds()) * order.price_per_minute // 60
            + order.price_unlock
        )
        dr.clear_money_for_order(order.user_id, order_id, order.total_amount)

    orders_repo.update_order_finish(conn, order)
    return order


def get_order(order_id: str, conn: Connection) -> Optional[OrderData]:
    return orders_repo.get_order(conn, order_id)
